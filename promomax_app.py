import re
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(
    page_title='Optimizador de precios y promociones',
    layout='wide',
    initial_sidebar_state='expanded'
)

COLUMN_MAP = {
    'sku': ['sku', 'id', 'id_producto', 'producto_id', 'product_id', 'product', 'codigo', 'codigo_producto', 'item', 'articulo'],
    'precio': ['precio', 'price', 'precio_unitario', 'precio unitario', 'valor unitario', 'unit price', 'pvp', 'precio venta'],
    'costo': ['costo', 'cost', 'costo_unitario', 'costo unitario', 'cost_unit', 'cost unit', 'coste'],
    'cantidad_vendida': ['cantidad', 'cantidad_vendida', 'unidades', 'qty', 'quantity', 'cantidad vendida', 'units', 'volumen'],
    'ventas': ['ventas', 'sales', 'ingresos', 'revenue', 'monto', 'valor', 'total_ventas', 'total'],
    'elasticidad': ['elasticidad', 'elasticity', 'elas', 'elasticidad_precio'],
    'categoria': ['categoria', 'category', 'categoría', 'segmento', 'grupo'],
    'region': ['region', 'región', 'territorio', 'area', 'zona'],
    'fecha': ['fecha', 'date', 'fecha_venta', 'fecha venta', 'sale_date', 'fecha de venta', 'date_venta'],
    'promocion': ['promocion', 'promo', 'descuento', 'tiene_descuento', 'descuento_flag', 'flag_promocion']
}

SCENARIOS = {
    'Precio +10%': 0.10,
    'Precio -10%': -0.10,
    'Promoción 2x1': -0.50,
    'Promoción 3x2': -0.3333,
    'Promoción 2° al 50%': -0.25,
}

REQUIRED_FIELDS = ['sku', 'precio']
OPTIONAL_FIELDS = ['costo', 'cantidad_vendida', 'ventas', 'elasticidad', 'categoria', 'region', 'fecha', 'promocion']


def clean_column_name(name):
    if name is None:
        return ''
    return re.sub(r'[^a-z0-9]', '', str(name).strip().lower())


def find_best_column(columns, candidates):
    clean_cols = {clean_column_name(col): col for col in columns}
    for alias in candidates:
        alias_clean = clean_column_name(alias)
        if alias_clean in clean_cols:
            return clean_cols[alias_clean]
    for col in columns:
        col_clean = clean_column_name(col)
        for alias in candidates:
            alias_clean = clean_column_name(alias)
            if alias_clean and alias_clean in col_clean:
                return col
    return None


def auto_map_columns(columns):
    mapping = {}
    for key, aliases in COLUMN_MAP.items():
        mapped = find_best_column(columns, aliases)
        if mapped:
            mapping[key] = mapped
    return mapping


def load_file(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        if uploaded_file.name.lower().endswith(('.xls', '.xlsx')):
            return pd.read_excel(uploaded_file)
        return pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f'No se pudo leer el archivo {uploaded_file.name}: {exc}')
        return None


def normalize_discount(series):
    if series is None:
        return pd.Series([], dtype='Int64')
    values = series.astype(str).str.lower().str.strip()
    values = values.replace({'true': '1', 'false': '0', 'si': '1', 'sí': '1', 'no': '0', 'yes': '1', 'y': '1', 'n': '0'})
    numeric = pd.to_numeric(values.str.replace('%', '', regex=False).str.replace(',', '.', regex=False), errors='coerce')
    result = pd.Series(np.where(numeric.notna() & numeric > 0, 1, np.where(numeric == 0, 0, np.nan)), index=series.index)
    result = result.fillna(values.map({'1': 1, '0': 0}))
    result = result.fillna(np.where(values.str.contains('desc|promo|discount|rebaja', na=False), 1, np.where(values.str.contains('sin|no|none|0', na=False), 0, np.nan)))
    return result.astype('Int64')


def build_mapping_ui(columns, auto_map):
    st.subheader('Mapeo de columnas')
    st.write('Revisa y corrige el mapeo automático si es necesario. Debes mapear al menos SKU y Precio.')
    mapped = {}
    choices = ['-'] + list(columns)
    for field in REQUIRED_FIELDS + OPTIONAL_FIELDS:
        default = auto_map.get(field, '-')
        index = choices.index(default) if default in choices else 0
        mapped[field] = st.selectbox(field.replace('_', ' ').capitalize(), choices, index=index)
    duplicates = [item for item in mapped.values() if item != '-' and list(mapped.values()).count(item) > 1]
    if duplicates:
        st.warning('Hay columnas seleccionadas más de una vez: ' + ', '.join(set(duplicates)))
    return {k: v for k, v in mapped.items() if v != '-'}


def prepare_sales_data(df, mapping, elasticity_df=None, global_elasticity=None):
    df = df.copy()
    rename = {mapping[k]: k for k in mapping if k in mapping and mapping[k]}
    df = df.rename(columns=rename)

    if 'ventas' not in df.columns and {'precio', 'cantidad_vendida'}.issubset(df.columns):
        df['ventas'] = df['precio'] * df['cantidad_vendida']
    if 'cantidad_vendida' not in df.columns and {'ventas', 'precio'}.issubset(df.columns):
        df['cantidad_vendida'] = df['ventas'] / df['precio']

    if 'costo' not in df.columns:
        df['costo'] = np.nan
    if 'categoria' not in df.columns:
        df['categoria'] = 'Sin categoría'
    if 'region' not in df.columns:
        df['region'] = 'Sin región'
    if 'promocion' in df.columns:
        df['promocion'] = normalize_discount(df['promocion']).fillna(0).astype('Int64')
    else:
        df['promocion'] = 0

    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)

    if elasticity_df is not None:
        elasticity_df = elasticity_df.copy()
        ext_map = auto_map_columns(list(elasticity_df.columns))
        if 'sku' in ext_map and 'elasticidad' in ext_map:
            elasticity_df = elasticity_df.rename(columns={ext_map['sku']: 'sku', ext_map['elasticidad']: 'elasticidad'})
            elasticity_df = elasticity_df[['sku', 'elasticidad']].dropna(subset=['sku'])
            df = df.merge(elasticity_df, on='sku', how='left', suffixes=('', '_ext'))
            if 'elasticidad_ext' in df.columns:
                df['elasticidad'] = df['elasticidad_ext']
                df = df.drop(columns=['elasticidad_ext'])

    if 'elasticidad' not in df.columns:
        df['elasticidad'] = np.nan

    if global_elasticity is not None:
        df['elasticidad'] = df['elasticidad'].fillna(global_elasticity)

    df['precio'] = pd.to_numeric(df['precio'], errors='coerce')
    df['costo'] = pd.to_numeric(df['costo'], errors='coerce')
    df['cantidad_vendida'] = pd.to_numeric(df['cantidad_vendida'], errors='coerce')
    df['ventas'] = pd.to_numeric(df['ventas'], errors='coerce')
    df['elasticidad'] = pd.to_numeric(df['elasticidad'], errors='coerce')

    if 'ventas' not in df.columns or df['ventas'].isna().all():
        df['ventas'] = df['precio'] * df['cantidad_vendida']

    df['margen_base'] = np.where(~df['costo'].isna(), df['precio'] - df['costo'], np.nan)
    df['margen_total_actual'] = np.where(~df['costo'].isna() & ~df['cantidad_vendida'].isna(), (df['precio'] - df['costo']) * df['cantidad_vendida'], np.nan)
    return df


def estimate_elasticity(df, default_elasticity=-1.0):
    df = df.copy()
    if 'elasticidad' in df.columns and df['elasticidad'].notna().any():
        df['elasticidad'] = df['elasticidad'].fillna(df['elasticidad'].median())
    else:
        df['elasticidad'] = np.nan

    estimates = {}
    global_values = []
    grouped = df.dropna(subset=['precio', 'cantidad_vendida']).copy()
    grouped = grouped[(grouped['precio'] > 0) & (grouped['cantidad_vendida'] > 0)]
    for sku, group in grouped.groupby('sku', observed=True):
        if len(group) >= 2:
            x = np.log(group['precio'].astype(float))
            y = np.log(group['cantidad_vendida'].astype(float))
            slope = np.polyfit(x, y, 1)[0]
            if slope < 0:
                estimates[sku] = slope
                global_values.append(slope)

    global_elasticity = np.median(global_values) if len(global_values) else default_elasticity
    df['elasticidad_estimado'] = df['sku'].map(estimates)
    df['elasticidad'] = df['elasticidad'].fillna(df['elasticidad_estimado'])
    df['elasticidad'] = df['elasticidad'].fillna(global_elasticity)
    return df, global_elasticity


def apply_scenario(df, scenario_name, custom_pct=0.0):
    discount = SCENARIOS.get(scenario_name, custom_pct / 100.0)
    if scenario_name == 'Descuento personalizado':
        discount = custom_pct / 100.0

    effective_price = df['precio'] * (1 + discount)
    predicted_qty = df['cantidad_vendida'] * (1 + df['elasticidad'] * discount)
    predicted_qty = predicted_qty.clip(lower=0)
    revenue = effective_price * predicted_qty
    margin = np.where(~df['costo'].isna(), (effective_price - df['costo']) * predicted_qty, np.nan)

    result = df.copy()
    result['scenario'] = scenario_name
    result['precio_simulado'] = effective_price
    result['cantidad_simulada'] = predicted_qty
    result['ventas_simuladas'] = revenue
    result['margen_simulado'] = margin
    return result


def recommend_action(row):
    if pd.isna(row['margen_actual']) or pd.isna(row['ventas_actuales']):
        return 'No recomendar'
    if row['mejor_escenario'] == 'Actual':
        return 'Mantener'
    if 'Precio +' in row['mejor_escenario']:
        return 'Subir'
    return 'Bajar'


def build_recommendations(df, custom_pct):
    base = df.groupby('sku', observed=True)[['ventas', 'margen_total_actual']].sum().reset_index()
    base = base.rename(columns={'ventas': 'ventas_actuales', 'margen_total_actual': 'margen_actual'})

    summaries = []
    for scenario in SCENARIOS.keys():
        scenario_df = apply_scenario(df, scenario)
        summary = scenario_df.groupby('sku', observed=True)[['ventas_simuladas', 'margen_simulado']].sum().reset_index()
        summary['scenario'] = scenario
        summaries.append(summary)
    if custom_pct is not None:
        scenario_df = apply_scenario(df, 'Descuento personalizado', custom_pct)
        summary = scenario_df.groupby('sku', observed=True)[['ventas_simuladas', 'margen_simulado']].sum().reset_index()
        summary['scenario'] = 'Descuento personalizado'
        summaries.append(summary)

    summary = pd.concat(summaries, ignore_index=True)
    best = summary.loc[summary.groupby('sku')['margen_simulado'].idxmax()].copy()
    merged = base.merge(best, on='sku', how='left')
    merged['mejor_escenario'] = merged['scenario']
    merged.loc[merged['margen_actual'] >= merged['margen_simulado'], ['mejor_escenario', 'ventas_simuladas', 'margen_simulado']] = ['Actual', merged['ventas_actuales'], merged['margen_actual']]
    merged['diferencia_ingreso_pct'] = np.where(merged['ventas_actuales'] != 0, (merged['ventas_simuladas'] - merged['ventas_actuales']) / merged['ventas_actuales'] * 100, np.nan)
    merged['diferencia_margen_pct'] = np.where(merged['margen_actual'] != 0, (merged['margen_simulado'] - merged['margen_actual']) / merged['margen_actual'] * 100, np.nan)
    merged['recomendacion'] = merged.apply(recommend_action, axis=1)
    merged = merged[['sku', 'mejor_escenario', 'recomendacion', 'ventas_actuales', 'margen_actual', 'ventas_simuladas', 'margen_simulado', 'diferencia_ingreso_pct', 'diferencia_margen_pct']]
    merged = merged.sort_values(by='margen_simulado', ascending=False)
    return merged


def format_dataframe(df):
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].round(2)
    return df


def get_dashboard_data(df, recommendations):
    metric_data = {
        'SKUs únicos': df['sku'].nunique(),
        'Ventas actuales totales': df['ventas'].sum(),
        'Margen total actual': df['margen_total_actual'].sum(skipna=True),
        'Elasticidad promedio': df['elasticidad'].mean(),
        'Promoción activa (%)': df['promocion'].mean() * 100 if 'promocion' in df.columns else np.nan,
    }
    best_actions = recommendations['recomendacion'].value_counts().to_dict()
    top_skus = df.groupby('sku', observed=True)[['ventas', 'margen_total_actual']].sum().reset_index().sort_values('ventas', ascending=False).head(10)
    by_category = df.groupby('categoria', observed=True)[['ventas', 'margen_total_actual']].sum().reset_index().sort_values('ventas', ascending=False).head(10)
    return metric_data, best_actions, top_skus, by_category


def render_dashboard(df, recommendations):
    st.subheader('Dashboard de análisis')
    metric_data, best_actions, top_skus, by_category = get_dashboard_data(df, recommendations)

    cols = st.columns(5)
    for index, (label, value) in enumerate(metric_data.items()):
        if index < len(cols):
            cols[index].metric(label, f'{value:,.2f}' if isinstance(value, (int, float, np.floating, np.integer)) else str(value))

    st.markdown('### Acciones recomendadas por SKU')
    action_df = pd.DataFrame([{'Acción': k, 'Cantidad de SKUs': v} for k, v in best_actions.items()])
    st.bar_chart(data=action_df.set_index('Acción'))

    st.markdown('### Top 10 SKUs por ventas actuales')
    st.bar_chart(data=top_skus.set_index('sku')[['ventas']])

    if not by_category.empty:
        st.markdown('### Top 10 categorías por ventas actuales')
        st.bar_chart(data=by_category.set_index('categoria')[['ventas']])

    st.markdown('### Resumen de ventas y margen por SKU')
    st.dataframe(format_dataframe(top_skus.rename(columns={'margen_total_actual': 'margen_actual'})))


def main():
    st.title('Optimizador de precios y promociones')
    st.markdown(
        'Carga tu archivo de ventas y mapea las columnas para utilizar el modelo. El sistema calcula precio, ingresos, margen base, estima elasticidad, simula escenarios avanzados y recomienda acciones por SKU.'
    )

    st.sidebar.header('Configuración del modelo')
    sales_file = st.sidebar.file_uploader('Archivo de ventas (CSV / Excel)', type=['csv', 'xls', 'xlsx'])
    elasticity_file = st.sidebar.file_uploader('Archivo de elasticidad opcional (CSV / Excel)', type=['csv', 'xls', 'xlsx'])
    use_manual_elasticity = st.sidebar.checkbox('Usar elasticidad global manual si no está disponible', value=True)
    manual_elasticity = st.sidebar.number_input('Elasticidad global por defecto', value=-1.0, step=0.1, format='%.2f') if use_manual_elasticity else None
    st.sidebar.markdown('---')
    scenario_choice = st.sidebar.selectbox('Escenario específico (opcional):', list(SCENARIOS.keys()) + ['Descuento personalizado'])
    custom_pct = None
    if scenario_choice == 'Descuento personalizado':
        custom_pct = st.sidebar.slider('Descuento personalizado (%)', min_value=-50, max_value=0, value=-10, step=1)

    if sales_file is None:
        st.warning('Carga primero el archivo de ventas para empezar.')
        return

    sales_df = load_file(sales_file)
    if sales_df is None:
        return

    st.subheader('Columnas detectadas')
    st.write(list(sales_df.columns))

    auto_map = auto_map_columns(list(sales_df.columns))
    mapping = build_mapping_ui(list(sales_df.columns), auto_map)

    if 'sku' not in mapping or 'precio' not in mapping:
        st.error('Debes mapear al menos las columnas SKU y Precio para continuar.')
        return

    elasticity_df = load_file(elasticity_file) if elasticity_file is not None else None
    sales_df = prepare_sales_data(sales_df, mapping, elasticity_df=elasticity_df, global_elasticity=manual_elasticity)

    if sales_df['cantidad_vendida'].isna().all() and sales_df['ventas'].isna().all():
        st.error('No se pudo calcular ni encontrar cantidad ni ventas. Revisa el mapeo y los datos.')
        return

    sales_df, global_elast = estimate_elasticity(sales_df, default_elasticity=manual_elasticity if manual_elasticity is not None else -1.0)

    recommendations = build_recommendations(sales_df, custom_pct if scenario_choice == 'Descuento personalizado' else None)

    tab_dashboard, tab_recommendations, tab_data = st.tabs(['Dashboard', 'Recomendaciones', 'Datos brutos'])

    with tab_dashboard:
        render_dashboard(sales_df, recommendations)

    with tab_recommendations:
        st.subheader('Recomendaciones por SKU')
        st.write('Las recomendaciones son el resultado de comparar escenarios de precio y margen para cada SKU.')
        st.dataframe(format_dataframe(recommendations.head(100)))

        st.download_button(
            'Descargar recomendaciones a CSV',
            data=recommendations.to_csv(index=False).encode('utf-8'),
            file_name='recomendaciones_por_sku.csv',
            mime='text/csv'
        )

        st.markdown('---')
        st.markdown('### Cómo funciona la recomendación')
        st.markdown(
            '- El cálculo prioriza el margen estimado por SKU.\n'
            '- Si el mejor escenario indica una promoción más agresiva, la recomendación será `Bajar`.\n'
            '- Si un aumento de precio mejora el margen, la recomendación será `Subir`.\n'
            '- Si el estado actual es el mejor, la recomendación será `Mantener`.\n'
            '- Si falta información confiable, la recomendación será `No recomendar`.'
        )

    with tab_data:
        st.subheader('Vista previa de los datos procesados')
        preview_columns = ['sku', 'precio', 'costo', 'cantidad_vendida', 'ventas', 'margen_base', 'margen_total_actual', 'elasticidad', 'promocion']
        preview_columns = [col for col in preview_columns if col in sales_df.columns]
        st.dataframe(format_dataframe(sales_df[preview_columns].head(50)))

        st.markdown('**Elasticidad de referencia usada:** ' + f'{global_elast:.2f}')
        st.markdown('**Número de SKUs únicos:** ' + f'{sales_df["sku"].nunique()}')
        st.markdown('**Ventas actuales totales:** ' + f'{sales_df["ventas"].sum():,.2f}')
        if 'margen_total_actual' in sales_df.columns:
            st.markdown('**Margen total actual estimado:** ' + f'{sales_df["margen_total_actual"].sum(skipna=True):,.2f}')


if __name__ == '__main__':
    main()
