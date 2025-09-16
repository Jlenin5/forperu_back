import openpyxl
import json
from .calculate import calculate_prices, find_price_by_name, parse_float, PriceType

def parse_excel(file, user_id):
  products = []
    
  try:
    workbook = openpyxl.load_workbook(file)
    sheet = workbook.active
    
    # Leer encabezados
    headers = [cell.value for cell in sheet[1]]
    header_map = {header: idx for idx, header in enumerate(headers) if header}
    
    # Validar encabezados requeridos
    required_headers = [
      "Codigo", "Nombre",
      "P.(CF) %", "P.(SF) %", "P.(Caja) %", "Costo",
      "Unidad"
      ]
    for req in required_headers:
      if req not in header_map:
        raise ValueError(f"Falta el encabezado requerido: {req}")
    
    # Definir el rango progresivo de porcentajes
    percentage_sequence = [
      1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16,
      20, 24, 26, 28, 30, 32, 34, 37,
      40, 43, 46, 49, 52, 55, 58, 61, 64, 67, 70
    ]

    # Generar lista de precios dinámicamente
    prices = [
      {"id": pct, "name": f"price_{pct}", "percentage": pct}
      for idx, pct in enumerate(percentage_sequence)
    ]
    
    # Iterar sobre las filas
    for row in sheet.iter_rows(min_row=2, values_only=True):
      if not any(row):  # Saltar filas vacías
        continue
            
      cost = parse_float(row[header_map["Costo"]])
        
      # Calcular precios
      calculated_cf = calculate_prices(prices, PriceType.CF, cost)
      calculated_sf = calculate_prices(prices, PriceType.SF, cost)
      calculated_box = calculate_prices(prices, PriceType.BOX, cost)
        
      # Obtener precios destacados
      def get_featured_price(price_type, price_key, calculated_prices):
        try:
          price_number = int(row[header_map[price_key]])
          price_name = f"price_{price_number}"
          found_price, exists = find_price_by_name(calculated_prices, price_name)
          return found_price['price'] if exists else 0.0
        except (ValueError, TypeError):
          return 0.0
        
      price_cf = get_featured_price(PriceType.CF, "P.(CF) %", calculated_cf)
      price_sf = get_featured_price(PriceType.SF, "P.(SF) %", calculated_sf)
      price_box = get_featured_price(PriceType.BOX, "P.(Caja) %", calculated_box)
        
        # Crear producto
      product = {
        "sku": row[header_map["Codigo"]] if row[header_map["Codigo"]] else None,
        "name": row[header_map["Nombre"]],
        "prices_cf": calculated_cf,
        "prices_sf": calculated_sf,
        "prices_box": calculated_box,
        "featured_pcf": price_cf if row[header_map["P.(CF) %"]] else None,
        "featured_psf": price_sf if row[header_map["P.(SF) %"]] else None,
        "featured_pbox": price_box if row[header_map["P.(Caja) %"]] else None,
        "unit": row[header_map["Unidad"]],
        "cost": cost,
        "created_by": user_id
      }
        
      products.append(product)
            
  except Exception as e:
    raise ValueError(f"Error procesando archivo Excel: {str(e)}")
    
  return products