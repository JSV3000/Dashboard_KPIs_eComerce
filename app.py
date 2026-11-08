import streamlit as st
import pandas as pd
import numpy as np

# Parche de compatibilidad para NumPy 2.x con Bokeh 2.4.3
np.bool8 = np.bool_

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter
from bokeh.transform import dodge
from bokeh.embed import file_html
from bokeh.resources import CDN
import streamlit.components.v1 as components

# Configuracion de la pagina y estilo oscuro (#0E1117)
st.set_page_config(
    page_title="Dashboard E-Commerce KPIs",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 16px;
        border-radius: 10px;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #C9D1D9 !important;
        font-weight: 600;
    }
    h1, h2, h3, p {
        color: #FAFAFA !important;
    }
    </style>
""", unsafe_allow_html=True)

# Renderizar cada grafico de Bokeh ocupando el 100% de su columna
def mostrar_bokeh(fig, height=340):
    fig.sizing_mode = "stretch_width"
    fig.background_fill_color = "#161B22"
    fig.border_fill_color = "#161B22"
    fig.outline_line_color = "#30363D"
    fig.title.text_color = "#FAFAFA"
    fig.xaxis.major_label_text_color = "#C9D1D9"
    fig.yaxis.major_label_text_color = "#C9D1D9"
    fig.xaxis.axis_label_text_color = "#C9D1D9"
    fig.yaxis.axis_label_text_color = "#C9D1D9"
    fig.xaxis.axis_line_color = "#30363D"
    fig.yaxis.axis_line_color = "#30363D"
    fig.xgrid.grid_line_color = "#21262D"
    fig.ygrid.grid_line_color = "#21262D"
    
    html = file_html(fig, CDN)
    components.html(html, height=height + 25)

# Generacion de datos simulados (12 meses)
@st.cache_data
def generar_datos(semilla=42):
    np.random.seed(semilla)
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    visitas = np.random.randint(18000, 32000, size=12) + np.linspace(0, 12000, 12).astype(int)
    tasa_conv_base = np.random.uniform(0.025, 0.042, size=12)
    pedidos = (visitas * tasa_conv_base).astype(int)
    
    ticket_promedio_base = np.random.uniform(750, 1150, size=12)
    ventas = np.round(pedidos * ticket_promedio_base, 2)
    
    proporcion_nuevos = np.random.uniform(0.55, 0.70, size=12)
    clientes_nuevos = (pedidos * proporcion_nuevos).astype(int)
    clientes_recurrentes = pedidos - clientes_nuevos
    
    satisfaccion = np.round(np.random.uniform(4.1, 4.9, size=12), 2)
    
    df = pd.DataFrame({
        'Mes': meses,
        'Visitas': visitas,
        'Pedidos': pedidos,
        'Ventas_Totales': ventas,
        'Valor_Promedio_Pedido': np.round(ventas / pedidos, 2),
        'Tasa_Conversion': np.round((pedidos / visitas) * 100, 2),
        'Clientes_Nuevos': clientes_nuevos,
        'Clientes_Recurrentes': clientes_recurrentes,
        'Satisfaccion': satisfaccion
    })
    return df

# Barra lateral para controles interactivos
st.sidebar.header("Configuracion")
semilla = st.sidebar.slider("Semilla de simulacion", min_value=1, max_value=100, value=42)
df = generar_datos(semilla)

rango_meses = st.sidebar.multiselect(
    "Filtrar meses:",
    options=df['Mes'].tolist(),
    default=df['Mes'].tolist()
)

df_filtrado = df[df['Mes'].isin(rango_meses)] if rango_meses else df

# Titulo principal
st.title("Dashboard de KPIs - E-Commerce")
st.markdown("Monitoreo anual de rendimiento comercial, conversion y retencion de clientes.")
st.markdown("Trabajo hecho por Josue Sifuentes Valdez - Daniel Croche Soto")

# Metricas clave en tarjetas
ventas_totales = df_filtrado['Ventas_Totales'].sum()
pedidos_totales = df_filtrado['Pedidos'].sum()
visitas_totales = df_filtrado['Visitas'].sum()
aov_global = ventas_totales / pedidos_totales if pedidos_totales > 0 else 0
cr_global = (pedidos_totales / visitas_totales) * 100 if visitas_totales > 0 else 0
sat_promedio = df_filtrado['Satisfaccion'].mean()
pct_recurrentes = (df_filtrado['Clientes_Recurrentes'].sum() / pedidos_totales) * 100 if pedidos_totales > 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Ventas Totales", f"${ventas_totales:,.0f}", f"{((df_filtrado['Ventas_Totales'].iloc[-1] / df_filtrado['Ventas_Totales'].mean()) - 1)*100:.1f}% últ. mes")
col2.metric("Total Pedidos", f"{pedidos_totales:,}", f"{df_filtrado['Pedidos'].iloc[-1]} últ. mes")
col3.metric("Ticket Promedio", f"${aov_global:,.2f}", f"${df_filtrado['Valor_Promedio_Pedido'].iloc[-1] - aov_global:,.1f} últ. mes")
col4.metric("Conversión", f"{cr_global:.2f}%", f"{df_filtrado['Tasa_Conversion'].iloc[-1] - cr_global:.2f}% últ. mes")
col5.metric("Retención", f"{pct_recurrentes:.1f}%", "Recurrentes")
col6.metric("⭐ Satisfacción", f"{sat_promedio:.2f} / 5.0", f"{df_filtrado['Satisfaccion'].iloc[-1] - sat_promedio:+.2f} últ. mes")

st.markdown("---")

meses_lista = df_filtrado['Mes'].tolist()

# Graficos con Bokeh (cada uno con su propio ColumnDataSource)
g_col1, g_col2 = st.columns(2)

with g_col1:
    source_ventas = ColumnDataSource(df_filtrado)
    p_ventas = figure(
        x_range=meses_lista, height=340,
        title="Ventas Totales en el año",
        toolbar_location="above", tools="pan,wheel_zoom,box_zoom,reset,save"
    )
    p_ventas.line(x='Mes', y='Ventas_Totales', source=source_ventas, line_width=3, color="#00D4FF", legend_label="Ventas ($)")
    p_ventas.circle(x='Mes', y='Ventas_Totales', source=source_ventas, size=8, color="#00D4FF", fill_color="#0E1117", line_width=2)
    p_ventas.yaxis.formatter = NumeralTickFormatter(format="$0,0")
    p_ventas.add_tools(HoverTool(tooltips=[("Mes", "@Mes"), ("Ventas", "$@Ventas_Totales{0,0.00}"), ("Ticket Prom.", "$@Valor_Promedio_Pedido{0,0.00}")]))
    p_ventas.legend.location = "top_left"
    p_ventas.legend.background_fill_color = "#0E1117"
    p_ventas.legend.label_text_color = "#FAFAFA"
    mostrar_bokeh(p_ventas, height=340)

with g_col2:
    source_pedidos = ColumnDataSource(df_filtrado)
    p_pedidos = figure(
        x_range=meses_lista, height=340,
        title="Pedidos Mensuales",
        toolbar_location="above", tools="pan,wheel_zoom,box_zoom,reset,save"
    )
    p_pedidos.vbar(x='Mes', top='Pedidos', source=source_pedidos, width=0.55, color="#7C3AED", line_color="#A78BFA")
    p_pedidos.y_range.start = 0
    p_pedidos.add_tools(HoverTool(tooltips=[("Mes", "@Mes"), ("Pedidos", "@Pedidos{0,0}"), ("Conversion", "@Tasa_Conversion%")]))
    mostrar_bokeh(p_pedidos, height=340)

# Clientes Nuevos vs Recurrentes y Satisfaccion del Cliente
g_col3, g_col4 = st.columns(2)

with g_col3:
    source_clientes = ColumnDataSource(df_filtrado)
    p_clientes = figure(
        x_range=meses_lista, height=340,
        title="Clientes Nuevos vs Recurrentes",
        toolbar_location="above", tools="pan,wheel_zoom,box_zoom,reset,save"
    )
    p_clientes.line(x='Mes', y='Clientes_Nuevos', source=source_clientes, line_width=3, color="#10B981", legend_label="Nuevos")
    p_clientes.circle(x='Mes', y='Clientes_Nuevos', source=source_clientes, size=7, color="#10B981")
    
    p_clientes.line(x='Mes', y='Clientes_Recurrentes', source=source_clientes, line_width=3, color="#F59E0B", legend_label="Recurrentes")
    p_clientes.circle(x='Mes', y='Clientes_Recurrentes', source=source_clientes, size=7, color="#F59E0B")
    
    p_clientes.add_tools(HoverTool(tooltips=[("Mes", "@Mes"), ("Nuevos", "@Clientes_Nuevos"), ("Recurrentes", "@Clientes_Recurrentes")]))
    p_clientes.legend.location = "top_left"
    p_clientes.legend.background_fill_color = "#0E1117"
    p_clientes.legend.label_text_color = "#FAFAFA"
    mostrar_bokeh(p_clientes, height=340)

with g_col4:
    source_sat = ColumnDataSource(df_filtrado)
    p_sat = figure(
        x_range=meses_lista, y_range=(3.5, 5.2), height=340,
        title="Evolucion de Satisfaccion del Cliente (CSAT)",
        toolbar_location="above", tools="pan,wheel_zoom,box_zoom,reset,save"
    )
    p_sat.vbar(x=dodge('Mes', 0.0, range=p_sat.x_range), top='Satisfaccion', source=source_sat, width=0.45, color="#EC4899", alpha=0.85)
    p_sat.line(x='Mes', y='Satisfaccion', source=source_sat, line_width=2, color="#FBBF24", line_dash="dashed", legend_label="Tendencia CSAT")
    p_sat.add_tools(HoverTool(tooltips=[("Mes", "@Mes"), ("Calificacion", "@Satisfaccion / 5.0")]))
    p_sat.legend.location = "bottom_right"
    p_sat.legend.background_fill_color = "#0E1117"
    p_sat.legend.label_text_color = "#FAFAFA"
    mostrar_bokeh(p_sat, height=340)

st.markdown("---")

# Tabla con los datos mensuales
st.subheader("Registro Detallado de Datos Mensuales")
st.dataframe(
    df_filtrado.style.format({
        'Visitas': '{:,}',
        'Pedidos': '{:,}',
        'Ventas_Totales': '${:,.2f}',
        'Valor_Promedio_Pedido': '${:,.2f}',
        'Tasa_Conversion': '{:.2f}%',
        'Clientes_Nuevos': '{:,}',
        'Clientes_Recurrentes': '{:,}',
        'Satisfaccion': '{:.2f}'
    }),
    use_container_width=True,
    hide_index=True
)

