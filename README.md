# Optimizador de precios y promociones

Esta aplicación permite subir un archivo de ventas (`CSV` o `Excel`), mapear columnas a las variables del modelo, calcular precio, ingresos y margen base, estimar elasticidad, simular escenarios de precio y promociones (2x1, 3x2, 2° al 50%, descuentos personalizados), visualizar un dashboard de análisis por SKU y exportar recomendaciones a CSV.

## Características principales

- Carga de archivos `CSV` o `Excel`
- Mapeo de columnas automático y edición manual
- Cálculo automático de ingresos y margen cuando faltan columnas
- Estimación de elasticidad por SKU o uso de elasticidad cargada por el usuario
- Simulación de escenarios de precio y promociones complejas
- Recomendaciones por SKU: `Subir`, `Bajar`, `Mantener`, `No recomendar`
- Exportación de resultados a un archivo `recomendaciones_por_sku.csv`

## Archivos importantes

- `promomax_app.py` — aplicación principal de Streamlit
- `requirements.txt` — dependencias de Python
- `README.md` — esta documentación

## Cómo usar localmente

1. Instala dependencias:

```bash
pip install -r requirements.txt
```

2. Ejecuta la aplicación:

```bash
streamlit run promomax_app.py
```

O simplemente haz doble clic en `run_app.bat`.

3. Abre la URL que Streamlit muestra en el navegador.

> Nota: esta aplicación se ejecuta localmente con Streamlit. No es una página web estática, por lo que no funcionará solo haciendo clic en una URL de GitHub Pages.

## Formato de archivos

- El archivo de ventas debe incluir al menos las columnas de `SKU` y `Precio`.
- Opcionalmente puede incluir `Costo`, `Cantidad`, `Ventas`, `Elasticidad`, `Categoría`, `Región`, `Fecha`, `Promoción`.
- Si falta `Ventas`, se calcula como `Precio * Cantidad`.
- Si falta `Cantidad`, se intenta inferir con `Ventas / Precio`.

## Nota

Esta versión está diseñada para funcionar como aplicación de análisis y optimización desde el repositorio antes de subirlo a GitHub.
