import json
from enum import Enum

class PriceType(Enum):
  CF = "CF"
  SF = "SF"
  BOX = "BOX"

# Generar márgenes dinámicamente (1% → 70%)
def generate_price_margins():
  return {f"price_{i}": 1 + (i / 100) for i in range(1, 71)}

PRICE_MARGINS = {
  "CF": generate_price_margins(),
  "SF": generate_price_margins(),
  "BOX": generate_price_margins()
}

def calculate_prices(prices, price_type, cost):
  result = []
  
  try:
    margin_type = PriceType(price_type).value
  except ValueError:
    return result
  
  for p in prices:
    margin = PRICE_MARGINS[margin_type].get(p['name'], 1.01)  # Margen por defecto
    
    if price_type == PriceType.CF.value:
      calculated_price = (((cost / 1.18) * 1.06 * margin) * 1.18)
    else:
      calculated_price = cost * margin
    
    result.append({
      'id': p['id'],
      'name': p['name'],
      'price': calculated_price
    })
  
  return result

def generate_all_prices(cost):
  prices_cf = [
    {"id": i, "name": f"price_{i}", "price": (((cost / 1.18) * 1.06 * (1 + i / 100)) * 1.18)}
    for i in range(1, 71)
  ]
  prices_sf = [
    {"id": i, "name": f"price_{i}", "price": cost * (1 + i / 100)}
    for i in range(1, 71)
  ]
  prices_box = [
    {"id": i, "name": f"price_{i}", "price": cost * (1 + i / 100)}
    for i in range(1, 71)
  ]

  return {
    "prices_cf": prices_cf,
    "prices_sf": prices_sf,
    "prices_box": prices_box,
    "featured_pcf": prices_cf[0]["price"],  # por defecto el 1%
    "featured_psf": prices_sf[0]["price"],
    "featured_pbox": prices_box[0]["price"]
  }

def find_price_by_name(prices, name):
  for price in prices:
    if price['name'] == name:
      return price, True
  return None, False

def parse_float(value):
  try:
    return float(value)
  except (ValueError, TypeError):
    return 0.0