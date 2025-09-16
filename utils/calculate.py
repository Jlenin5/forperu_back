import json
from enum import Enum

class PriceType(Enum):
  CF = "CF"
  SF = "SF"
  BOX = "BOX"

# Reglas de incremento progresivo
INCREMENT_RULES = [
  {"start": 1, "end": 6, "step": 1},   # 1–6 en saltos de 1
  {"start": 6, "end": 34, "step": 2},  # 6–34 en saltos de 2
  {"start": 34, "end": 70, "step": 3}, # 34–70 en saltos de 3
]

# Generar márgenes dinámicamente (1% → 70%)
def generate_price_margins():
  margins = {}
  for rule in INCREMENT_RULES:
    i = rule["start"]
    while i <= rule["end"]:
      margins[f"price_{i}"] = 1 + (i / 100)
      i += rule["step"]
  return margins

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
    margin = PRICE_MARGINS[margin_type].get(p['name'])
    if not margin:
      continue
    
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
    {"id": idx, "name": name, "price": (((cost / 1.18) * 1.06 * margin) * 1.18)}
    for idx, (name, margin) in enumerate(PRICE_MARGINS["CF"].items(), start=1)
  ]
  prices_sf = [
    {"id": idx, "name": name, "price": cost * margin}
    for idx, (name, margin) in enumerate(PRICE_MARGINS["SF"].items(), start=1)
  ]
  prices_box = [
    {"id": idx, "name": name, "price": cost * margin}
    for idx, (name, margin) in enumerate(PRICE_MARGINS["BOX"].items(), start=1)
  ]

  return {
    "prices_cf": prices_cf,
    "prices_sf": prices_sf,
    "prices_box": prices_box,
    "featured_pcf": prices_cf[0]["price"] if prices_cf else None,
    "featured_psf": prices_sf[0]["price"] if prices_sf else None,
    "featured_pbox": prices_box[0]["price"] if prices_box else None
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