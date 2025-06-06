import streamlit as st
import pandas as pd
import pymysql
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- Conexión a MySQL ---
def get_mysql_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Wizardkiller#02',
        database='covid19',
        cursorclass=pymysql.cursors.Cursor
    )

# --- Cache por año ---
@st.cache_data(show_spinner="Cargando datos desde MySQL...")
def load_table_cached(table_name):
    try:
        connection = get_mysql_connection()
        with connection.cursor() as cursor:
            sql = f"SELECT * FROM {table_name}"
            cursor.execute(sql)
            columnas = [col[0] for col in cursor.description]
            datos = cursor.fetchall()
            df = pd.DataFrame(datos, columns=columnas)
            return df
    except Exception as e:
        st.error(f"Error al cargar {table_name}: {e}")
        return pd.DataFrame()
    finally:
        if connection:
            connection.close()

tablas = {
    "2020": "covid19_2020",
    "2021": "covid19_2021",
    "2022": "covid19_2022",
    "2023": "covid19_2023"
}

st.title("Dashboard de Datos COVID 19")

st.sidebar.header("Parámetros")
seleccion = st.sidebar.selectbox("Selecciona el año", list(tablas.keys()))

if "cache_dfs" not in st.session_state:
    st.session_state.cache_dfs = {}

if seleccion not in st.session_state.cache_dfs:
    st.session_state.cache_dfs[seleccion] = load_table_cached(tablas[seleccion])

df = st.session_state.cache_dfs[seleccion]

if not df.empty:
    st.success("Datos cargados correctamente.")

    st.sidebar.header("Filtros")

    regiones = df['REGION'].dropna().unique()
    region_seleccionada = st.sidebar.selectbox("Selecciona una Región", sorted(regiones))

    entidades = df[df['REGION'] == region_seleccionada]['ENTIDAD'].dropna().unique()
    entidad_seleccionada = st.sidebar.selectbox("Selecciona una Entidad Federativa", sorted(entidades))

    df_filtrado = df[
        (df['REGION'] == region_seleccionada) &
        (df['ENTIDAD'] == entidad_seleccionada)
    ]

    if st.sidebar.button("Actualizar datos"):
        if "cache_dfs" in st.session_state:
            del st.session_state.cache_dfs[seleccion]
    st.cache_data.clear()

else:
    st.warning("La tabla está vacía o ocurrió un error al cargar los datos.")

# KPIs
# Indicadores Clave
st.markdown("## Indicadores Clave")

# Filtrados para los KPIs
df_confirmados = df_filtrado[df_filtrado['CLASIFICACION_FINAL'] == 1]
total_confirmados = len(df_confirmados)
total_negativos = len(df_filtrado[df_filtrado['CLASIFICACION_FINAL'] == 2])
total_sospechosos = len(df_filtrado[df_filtrado['CLASIFICACION_FINAL'] == 3])

defunciones = df_confirmados[df_confirmados['FECHA_DEF'].notna() & (df_confirmados['FECHA_DEF'] != '9999-99-99')]
total_defunciones = len(defunciones)

if 'RECUPERADO' in df_confirmados.columns:
    df_confirmados['FECHA_DEF'] = df_confirmados['FECHA_DEF'].astype(str)
    total_recuperados = len(df_confirmados[df_confirmados['FECHA_DEF'] == '9999-99-99'])
else:
    total_recuperados = 0

hombres = len(df_confirmados[df_confirmados['SEXO'] == 1])
mujeres = len(df_confirmados[df_confirmados['SEXO'] == 2])
porc_hombres = round((hombres / total_confirmados) * 100, 1) if total_confirmados > 0 else 0
porc_mujeres = round((mujeres / total_confirmados) * 100, 1) if total_confirmados > 0 else 0

hospitalizados = len(df_confirmados[df_confirmados['TIPO_PACIENTE'] == 2])
ambulatorios = len(df_confirmados[df_confirmados['TIPO_PACIENTE'] == 1])
porc_hosp = round((hospitalizados / total_confirmados) * 100, 1) if total_confirmados > 0 else 0
porc_ambu = round((ambulatorios / total_confirmados) * 100, 1) if total_confirmados > 0 else 0

def porcentaje_condicion(col):
    if col in df_confirmados.columns:
        return round((len(df_confirmados[df_confirmados[col] == 1]) / total_confirmados) * 100, 1)
    return 0

comorbilidades = {
    "Diabetes": porcentaje_condicion("DIABETES"),
    "Hipertensión": porcentaje_condicion("HIPERTENSION"),
    "Obesidad": porcentaje_condicion("OBESIDAD"),
    "Renal Crónica": porcentaje_condicion("RENAL_CRONICA"),
    "Cardiovascular": porcentaje_condicion("CARDIOVASCULAR"),
    "Tabaquismo": porcentaje_condicion("TABAQUISMO")
}

# Diseño de las métricas en tarjetas

# Dividir los KPIs en columnas
# Diseño de las métricas en tarjetas

# Definir colores para cada categoría
color_confirmados = "#e74c3c"  # Rojo
color_negativos = "#3498db"    # Azul
color_sospechosos = "#f39c12"  # Naranja
color_defunciones = "#7f8c8d"  # Gris
color_recuperados = "#e67e22"  # Naranja oscuro
color_activos = "#2ecc71"      # Verde

# Crear una función para formatear números con comas
def format_number(num):
    return f"{num:,}".replace(",", ",")

st.markdown("""
<style>
.kpi-card {
    background-color: #1e1e2f;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    color: white;
    margin-bottom: 10px;
    min-height: 100px;
    position: relative;
    overflow: hidden;
    text-align: center;
}
.kpi-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 10px;
    color: rgba(255, 255, 255, 0.8);
}
.kpi-value {
    font-size: 24px;
    font-weight: 700;
}
.kpi-subtitle {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 5px;
}
.kpi-icon {
    position: absolute;
    right: 15px;
    top: 15px;
    opacity: 0.8;
    font-size: 20px;
}
.kpi-left-border {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    border-radius: 3px 0 0 3px;
}
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
""", unsafe_allow_html=True)

# Primera fila - 3 columnas
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_confirmados};"></div>
            <div class="kpi-icon"><i class="fas fa-virus"></i></div>
            <div class="kpi-title">CONFIRMADOS</div>
            <div class="kpi-value">{format_number(total_confirmados)}</div>
            <div class="kpi-subtitle">Casos acumulados</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_negativos};"></div>
            <div class="kpi-icon"><i class="fas fa-shield-virus"></i></div>
            <div class="kpi-title">NEGATIVOS</div>
            <div class="kpi-value">{format_number(total_negativos)}</div>
            <div class="kpi-subtitle">Casos acumulados</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_sospechosos};"></div>
            <div class="kpi-icon"><i class="fas fa-question-circle"></i></div>
            <div class="kpi-title">SOSPECHOSOS</div>
            <div class="kpi-value">{format_number(total_sospechosos)}</div>
            <div class="kpi-subtitle">Casos acumulados</div>
        </div>
    """, unsafe_allow_html=True)

# Segunda fila - 3 columnas
col4, col5, col6 = st.columns(3)
with col4:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_defunciones};"></div>
            <div class="kpi-icon"><i class="fas fa-procedures"></i></div>
            <div class="kpi-title">DEFUNCIONES</div>
            <div class="kpi-value">{format_number(total_defunciones)}</div>
            <div class="kpi-subtitle">Acumulados</div>
        </div>
    """, unsafe_allow_html=True)
with col5:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_recuperados};"></div>
            <div class="kpi-icon"><i class="fas fa-heartbeat"></i></div>
            <div class="kpi-title">RECUPERADOS</div>
            <div class="kpi-value">{format_number(total_recuperados)}</div>
            <div class="kpi-subtitle">Acumulados</div>
        </div>
    """, unsafe_allow_html=True)
with col6:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_activos};"></div>
            <div class="kpi-icon"><i class="fas fa-user-friends"></i></div>
            <div class="kpi-title">HOMBRES / MUJERES</div>
            <div class="kpi-value">{porc_hombres}% / {porc_mujeres}%</div>
            <div class="kpi-subtitle">Distribución por género</div>
        </div>
    """, unsafe_allow_html=True)

# Tercera fila - 2 columnas
col7, col8 = st.columns(2)
with col7:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_defunciones};"></div>
            <div class="kpi-icon"><i class="fas fa-hospital"></i></div>
            <div class="kpi-title">HOSPITALIZADOS</div>
            <div class="kpi-value">{porc_hosp}%</div>
            <div class="kpi-subtitle">Del total de confirmados</div>
        </div>
    """, unsafe_allow_html=True)
with col8:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_activos};"></div>
            <div class="kpi-icon"><i class="fas fa-home"></i></div>
            <div class="kpi-title">AMBULATORIOS</div>
            <div class="kpi-value">{porc_ambu}%</div>
            <div class="kpi-subtitle">Del total de confirmados</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

# Porcentaje de comorbilidades
st.markdown("### Comorbilidades Principales")

# Crear columnas para organizar las comorbilidades en fila
cols = st.columns(len(comorbilidades))

# Ordenar comorbilidades por valor descendente
sorted_comorbilidades = dict(sorted(comorbilidades.items(), key=lambda item: item[1], reverse=True))

# Mostrar cada comorbilidad en su propia columna con barra de progreso
for i, (nombre, valor) in enumerate(sorted_comorbilidades.items()):
    with cols[i]:
        st.markdown(f"**{nombre.upper()}**")
        # Crear barra de progreso con el color correspondiente
        if valor > 10:
            color = "#d73027"  # Rojo para valores altos
        elif valor > 7:
            color = "#fc8d59"  # Naranja para valores medios
        else:
            color = "#91bfdb"  # Azul para valores bajos
            
        # Mostrar valor numérico y barra
        st.markdown(f"{valor:.2f} %")
        st.markdown(
            f"""
            <div style="background-color: #f0f0f0; border-radius: 3px; height: 10px; width: 100%;">
                <div style="background-color: {color}; width: {min(valor*2, 100)}%; height: 100%; border-radius: 3px;"></div>
            </div>
            """, 
            unsafe_allow_html=True
        )

# Nota al pie
suma_total = sum(sorted_comorbilidades.values())

# Crear una línea divisoria
st.markdown("<hr style='margin: 15px 0 10px 0; border: 0; border-top: 1px solid #ccc;'>", unsafe_allow_html=True)

# Crear una barra para la suma total con todos los valores
st.markdown("<div style='padding: 8px 0;'>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 3])
with col1:
    st.markdown(f"**TOTAL DE LA POBLACIÓN**")
    st.markdown(f"{suma_total:.2f} %")
with col2:
    # Barra total con degradado para representar la combinación de todas las comorbilidades
    st.markdown(
        f"""
        <div style="background-color: #f0f0f0; border-radius: 3px; height: 12px; width: 100%; margin-top: 22px;">
            <div style="background: linear-gradient(90deg, #d73027, #fc8d59, #91bfdb); 
                        width: {min(suma_total, 100)}%; 
                        height: 100%; 
                        border-radius: 3px;"></div>
        </div>
        """, 
        unsafe_allow_html=True
    )
st.markdown("</div>", unsafe_allow_html=True)

# Nota al pie
# st.markdown("<span style='color: #777; font-size: 0.8em;'>* Porcentajes de Casos Confirmados</span>", unsafe_allow_html=True)

# Divisor visual para separar secciones
st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)


# Gráfico Edad-Sexo

# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución Demográfica por Edad y Sexo</h3>
</div>
""", unsafe_allow_html=True)

# Selector con estilo mejorado
col1, col2 = st.columns([3, 1])
with col2:
    tipo_caso = st.selectbox(
        "Tipo de caso:",
        ["Confirmados", "Negativos", "Sospechosos"],
        key="grafico_tipo_caso"
    )

tipo_map = {"Confirmados": 1, "Negativos": 2, "Sospechosos": 3}
tipo_color = {"Confirmados": "#e74c3c", "Negativos": "#3498db", "Sospechosos": "#f39c12"}
tipo_valor = tipo_map[tipo_caso]

# Preparación de datos
df_tipo = df[df['CLASIFICACION_FINAL'] == tipo_valor].copy()

# Definir rangos de edad más limpios
bins = list(range(0, 100, 5)) + [100]
labels = [f"{i}-{i+4}" for i in range(0, 95, 5)] + ["95+"]
df_tipo['RANGO_EDAD'] = pd.cut(df_tipo['EDAD'], bins=bins, labels=labels, right=False)
df_tipo['SEXO'] = df_tipo['SEXO'].map({1: "Hombres", 2: "Mujeres"})

# Agrupar por rango de edad y sexo
conteo = df_tipo.groupby(['RANGO_EDAD', 'SEXO']).size().reset_index(name='CASOS')

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado
fig, ax = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Colores personalizados
color_hombres = "#3498db"  # Azul para hombres
color_mujeres = "#e74c3c"  # Rojo para mujeres

# Crear gráfico de barras con colores personalizados y transparencia
bars = sns.barplot(
    data=conteo, 
    x="RANGO_EDAD", 
    y="CASOS", 
    hue="SEXO",
    palette={
        "Hombres": color_hombres,
        "Mujeres": color_mujeres
    },
    alpha=0.8,
    ax=ax
)

# Personalización avanzada del gráfico
ax.set_facecolor('#1e1e2f')
ax.set_title(f"Distribución por Edad y Sexo - {tipo_caso}", fontsize=16, pad=20, color='white')
ax.set_xlabel("Rango de Edad", fontsize=12, color='white')
ax.set_ylabel("Número de Casos", fontsize=12, color='white')

# Mejorar el diseño del eje X
plt.xticks(rotation=45, ha='right', color='white')
plt.yticks(color='white')
ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')

# Mejorar la leyenda
legend = ax.legend(title="Género", frameon=True, facecolor='#222244', edgecolor='gray')
legend.get_title().set_color('white')
for text in legend.get_texts():
    text.set_color('white')

# Añadir bordes sutiles a las barras para mejor visibilidad
for bar in ax.patches:
    bar.set_edgecolor('white')
    bar.set_linewidth(0.5)

# Añadir línea de contorno al gráfico
for spine in ax.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Añadir números en las barras para valores significativos
for bar in ax.patches:
    height = bar.get_height()
    if height > 0:
        if height > max(conteo["CASOS"]) * 0.05:  # Solo mostrar valores significativos
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                bar.get_height() + 5,
                f'{int(height):,}',
                ha='center', va='bottom',
                color='white', fontsize=8
            )

# Ajustar el diseño
plt.tight_layout()

# Añadir una nota o descripción
st.pyplot(fig)

# Datos adicionales contextuales
with st.expander("Detalles del análisis por rango de edad"):
    # Calcular algunos estadísticos interesantes
    total_hombres = conteo[conteo["SEXO"] == "Hombres"]["CASOS"].sum()
    total_mujeres = conteo[conteo["SEXO"] == "Mujeres"]["CASOS"].sum()
    
    # Encontrar el rango de edad con más casos para cada sexo
    max_hombres = conteo[conteo["SEXO"] == "Hombres"].sort_values("CASOS", ascending=False).iloc[0]
    max_mujeres = conteo[conteo["SEXO"] == "Mujeres"].sort_values("CASOS", ascending=False).iloc[0]
    
    # Mostrar estadísticas
    st.markdown(f"""
    <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
        <p style="color: white; margin: 0;">Total de casos en <span style="color: {color_hombres};">Hombres</span>: {total_hombres:,}</p>
        <p style="color: white; margin: 0;">Total de casos en <span style="color: {color_mujeres};">Mujeres</span>: {total_mujeres:,}</p>
        <p style="color: white; margin: 0;">Rango de edad más afectado en hombres: {max_hombres['RANGO_EDAD']} ({max_hombres['CASOS']:,} casos)</p>
        <p style="color: white; margin: 0;">Rango de edad más afectado en mujeres: {max_mujeres['RANGO_EDAD']} ({max_mujeres['CASOS']:,} casos)</p>
    </div>
    """, unsafe_allow_html=True)

    # =================== DIVISOR VISUAL ===================
st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

# Gráfico Edad - Tipo de Paciente
# Gráfico Edad - Tipo de Paciente con tema oscuro mejorado

# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución por Edad y Tipo de Atención</h3>
</div>
""", unsafe_allow_html=True)

# Selector con estilo mejorado
col1, col2 = st.columns([3, 1])
with col2:
    tipo_caso_tp = st.selectbox(
        "Tipo de caso:",
        ["Confirmados", "Negativos", "Sospechosos"],
        key="grafico_tipo_paciente"
    )

tipo_valor_tp = tipo_map[tipo_caso_tp]
df_tipo_tp = df[df['CLASIFICACION_FINAL'] == tipo_valor_tp].copy()

df_tipo_tp['TIPO_PACIENTE'] = df_tipo_tp['TIPO_PACIENTE'].map({1: "Ambulatorios", 2: "Hospitalizados"})
df_tipo_tp['RANGO_EDAD'] = pd.cut(df_tipo_tp['EDAD'], bins=list(range(0, 100, 5)) + [100], labels=labels, right=False)

conteo_tp = df_tipo_tp.groupby(['RANGO_EDAD', 'TIPO_PACIENTE']).size().reset_index(name='CASOS')

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado
fig2, ax2 = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig2.patch.set_facecolor('#1e1e2f')

# Colores personalizados
color_ambulatorio = "#2ecc71"  # Verde para ambulatorios
color_hospitalizado = "#e67e22"  # Naranja para hospitalizados

# Crear gráfico de barras con colores personalizados y transparencia
bars = sns.barplot(
    data=conteo_tp, 
    x="RANGO_EDAD", 
    y="CASOS", 
    hue="TIPO_PACIENTE",
    palette={
        "Ambulatorios": color_ambulatorio,
        "Hospitalizados": color_hospitalizado
    },
    alpha=0.8,
    ax=ax2
)

# Personalización avanzada del gráfico
ax2.set_facecolor('#1e1e2f')
ax2.set_title(f"Distribución por Edad y Tipo de Atención - {tipo_caso_tp}", fontsize=16, pad=20, color='white')
ax2.set_xlabel("Rango de Edad", fontsize=12, color='white')
ax2.set_ylabel("Número de Casos", fontsize=12, color='white')

# Mejorar el diseño del eje X
plt.xticks(rotation=45, ha='right', color='white')
plt.yticks(color='white')
ax2.grid(axis='y', linestyle='--', alpha=0.3, color='gray')

# Mejorar la leyenda
legend = ax2.legend(title="Tipo de Atención", frameon=True, facecolor='#222244', edgecolor='gray')
legend.get_title().set_color('white')
for text in legend.get_texts():
    text.set_color('white')

# Añadir bordes sutiles a las barras para mejor visibilidad
for bar in ax2.patches:
    bar.set_edgecolor('white')
    bar.set_linewidth(0.5)

# Añadir línea de contorno al gráfico
for spine in ax2.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Añadir números en las barras para valores significativos
for bar in ax2.patches:
    height = bar.get_height()
    if height > 0:
        if height > max(conteo_tp["CASOS"]) * 0.05:  # Solo mostrar valores significativos
            ax2.text(
                bar.get_x() + bar.get_width() / 2.,
                bar.get_height() + 5,
                f'{int(height):,}',
                ha='center', va='bottom',
                color='white', fontsize=8
            )

# Ajustar el diseño
plt.tight_layout()

# Mostrar gráfico
st.pyplot(fig2)

# Datos adicionales contextuales
with st.expander("Detalles del análisis por tipo de atención"):
    # Calcular algunos estadísticos interesantes
    total_ambulatorios = conteo_tp[conteo_tp["TIPO_PACIENTE"] == "Ambulatorios"]["CASOS"].sum()
    total_hospitalizados = conteo_tp[conteo_tp["TIPO_PACIENTE"] == "Hospitalizados"]["CASOS"].sum()
    
    # Encontrar el rango de edad con más casos para cada tipo
    max_ambulatorios = conteo_tp[conteo_tp["TIPO_PACIENTE"] == "Ambulatorios"].sort_values("CASOS", ascending=False).iloc[0]
    max_hospitalizados = conteo_tp[conteo_tp["TIPO_PACIENTE"] == "Hospitalizados"].sort_values("CASOS", ascending=False).iloc[0]
    
    # Calcular porcentajes
    total_casos = total_ambulatorios + total_hospitalizados
    porc_ambulatorios = (total_ambulatorios / total_casos) * 100 if total_casos > 0 else 0
    porc_hospitalizados = (total_hospitalizados / total_casos) * 100 if total_casos > 0 else 0
    
    # Mostrar estadísticas
    st.markdown(f"""
    <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
        <p style="color: white; margin: 0;">Total de casos <span style="color: {color_ambulatorio};">Ambulatorios</span>: {total_ambulatorios:,} ({porc_ambulatorios:.1f}%)</p>
        <p style="color: white; margin: 0;">Total de casos <span style="color: {color_hospitalizado};">Hospitalizados</span>: {total_hospitalizados:,} ({porc_hospitalizados:.1f}%)</p>
        <p style="color: white; margin: 0;">Rango de edad más frecuente en ambulatorios: {max_ambulatorios['RANGO_EDAD']} ({max_ambulatorios['CASOS']:,} casos)</p>
        <p style="color: white; margin: 0;">Rango de edad más frecuente en hospitalizados: {max_hospitalizados['RANGO_EDAD']} ({max_hospitalizados['CASOS']:,} casos)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas adicionales
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Relación Ambulatorios/Hospitalizados", 
            f"{(total_ambulatorios/total_hospitalizados):.2f}" if total_hospitalizados > 0 else "N/A", 
            help="Número de casos ambulatorios por cada hospitalizado"
        )
    with col2:
        # Calcular la edad promedio para cada tipo (usando el punto medio de cada rango)
        rangos_edad = {}
        for label in labels:
            if "-" in label:
                inicio = int(label.split("-")[0])
                fin = int(label.split("-")[1])
                rangos_edad[label] = (inicio + fin) / 2
            else:  # Para "95+"
                rangos_edad[label] = 97.5
                
        # Calcular edad promedia ponderada
        edad_prom_hosp = sum(rangos_edad[row['RANGO_EDAD']] * row['CASOS'] for _, row in conteo_tp[conteo_tp["TIPO_PACIENTE"] == "Hospitalizados"].iterrows()) / total_hospitalizados if total_hospitalizados > 0 else 0
        edad_prom_amb = sum(rangos_edad[row['RANGO_EDAD']] * row['CASOS'] for _, row in conteo_tp[conteo_tp["TIPO_PACIENTE"] == "Ambulatorios"].iterrows()) / total_ambulatorios if total_ambulatorios > 0 else 0
        
        st.metric(
            "Diferencia de edad promedio", 
            f"{abs(edad_prom_hosp - edad_prom_amb):.1f} años",
            f"{'Hospitalizados mayores' if edad_prom_hosp > edad_prom_amb else 'Ambulatorios mayores'}",
            help="Diferencia entre la edad promedio de hospitalizados y ambulatorios"
        )

st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

# Gráfico Barras Agrupadas por Resultado de Antígeno
# --- Gráfico de barras agrupadas: Pacientes por Mes y Resultado de Antígeno ---
# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Pacientes por Mes y Resultado de Antígeno</h3>
</div>
""", unsafe_allow_html=True)

# Preparación de datos mejorada
df['FECHA_INGRESO'] = pd.to_datetime(df['FECHA_INGRESO'], errors='coerce')
df_antigeno = df[df['FECHA_INGRESO'].notna()].copy()
df_antigeno['MES'] = df_antigeno['FECHA_INGRESO'].dt.month

# Agrupar por mes y resultado
conteo = df_antigeno.groupby(['MES', 'RESULTADO_ANTIGENO']).size().reset_index(name='PACIENTES')
pivotado = conteo.pivot(index='MES', columns='RESULTADO_ANTIGENO', values='PACIENTES').fillna(0)

# Asegurar que todos los meses estén presentes
for mes in range(1, 13):
    if mes not in pivotado.index:
        pivotado.loc[mes] = [0] * pivotado.shape[1]
pivotado = pivotado.sort_index()

# Etiquetas de meses y configuración de barras
labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
x = np.arange(len(labels))
width = 0.25  # ancho de cada barra
col_resultados = pivotado.columns.tolist()

# Mapeo de resultados a nombres legibles
resultados_nombres = {
    1: "Positivo",
    2: "Negativo",
    97: "No Aplicado",
    98: "Se Ignora",
    99: "No Especificado"
}

# Colores atractivos por resultado
colores_resultado = {
    1: "#e74c3c",  # Rojo para positivos
    2: "#2ecc71",  # Verde para negativos
    97: "#7f8c8d", # Gris para no aplicado
    98: "#f39c12", # Naranja para se ignora
    99: "#3498db"  # Azul para no especificado
}

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig, ax = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Dibujar barras agrupadas con colores personalizados
offset = -width
for i, col in enumerate(col_resultados):
    bars = ax.bar(
        x + offset, 
        pivotado[col], 
        width, 
        label=resultados_nombres.get(col, f"Resultado {col}"),
        color=colores_resultado.get(col, "#ffffff"),
        edgecolor='white',
        linewidth=0.5,
        alpha=0.8
    )
    
    # Añadir etiquetas a barras significativas
    umbral = max(pivotado[col]) * 0.1 if max(pivotado[col]) > 0 else 0  # Solo mostrar valores para barras con > 10% del máximo
    for j, bar in enumerate(bars):
        height = bar.get_height()
        if height > umbral:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 5,
                f'{int(height):,}',
                ha='center', va='bottom',
                color='white',
                fontsize=8,
                rotation=0,
                bbox=dict(boxstyle="round,pad=0.2", fc='#222244', alpha=0.7, ec="gray")
            )
    
    # Actualizar offset para la siguiente serie
    offset += width

# Personalización avanzada del gráfico
ax.set_facecolor('#1e1e2f')
ax.set_title("Evolución Mensual por Resultado de Antígeno", fontsize=16, pad=20, color='white')
ax.set_xlabel("Mes", fontsize=12, color='white', labelpad=10)
ax.set_ylabel("Número de Pacientes", fontsize=12, color='white', labelpad=10)

# Configurar eje X
ax.set_xticks(x)
ax.set_xticklabels(labels, color='white', fontsize=10)

# Configurar eje Y
ax.tick_params(axis='y', colors='white', labelsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')

# Mejorar la leyenda
legend = ax.legend(
    title="Resultado de Antígeno",
    frameon=True,
    facecolor='#222244',
    edgecolor='gray',
    fontsize=10,
    loc='upper right'
)
legend.get_title().set_color('white')
for text in legend.get_texts():
    text.set_color('white')

# Añadir línea de contorno al gráfico
for spine in ax.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Ajustar el diseño
plt.tight_layout()

# Mostrar gráfico
st.pyplot(fig)

# Añadir análisis adicional
with st.expander("Análisis detallado de resultados de antígeno"):
    # Calcular totales por resultado
    totales_por_resultado = pivotado.sum()
    
    # Encontrar mes con más casos para cada resultado
    meses_pico = {}
    for res in pivotado.columns:
        mes_pico = pivotado[res].idxmax()
        valor_pico = pivotado[res].max()
        meses_pico[res] = (mes_pico, valor_pico)
    
    # Mostrar estadísticas
    st.markdown("""
    <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
        <h4 style="color: white; margin-top: 0;">Totales por resultado de antígeno</h4>
    """, unsafe_allow_html=True)
    
    for res in pivotado.columns:
        color = colores_resultado.get(res, "#ffffff")
        nombre = resultados_nombres.get(res, f"Resultado {res}")
        total = totales_por_resultado[res]
        mes_pico, valor_pico = meses_pico[res]
        
        if total > 0:  # Solo mostrar resultados con datos
            st.markdown(f"""
            <p style="color: white; margin: 5px 0;">
                <span style="color: {color};">■</span> <strong>{nombre}</strong>: 
                {int(total):,} pruebas en total | 
                Pico en {labels[mes_pico-1]} con {int(valor_pico):,} pruebas
            </p>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Gráfico de pastel para la distribución total
    col1, col2 = st.columns(2)
    
    with col1:
        # Crear figura para pastel
        fig_pie, ax_pie = plt.subplots(figsize=(6, 6), facecolor='#1e1e2f')
        fig_pie.patch.set_facecolor('#1e1e2f')
        
        # Filtrar solo valores relevantes (>0)
        pie_data = [v for v in totales_por_resultado.values if v > 0]
        pie_labels = [resultados_nombres.get(c, f"Resultado {c}") for c, v in totales_por_resultado.items() if v > 0]
        pie_colors = [colores_resultado.get(c, "#ffffff") for c, v in totales_por_resultado.items() if v > 0]
        
        # Crear gráfico de pastel
        wedges, texts, autotexts = ax_pie.pie(
            pie_data,
            labels=None,  # Sin etiquetas directas, usaremos leyenda
            autopct='%1.1f%%',
            startangle=90,
            colors=pie_colors,
            wedgeprops=dict(width=0.5, edgecolor='white', linewidth=0.5)
        )
        
        # Personalizar textos
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')
        
        # Añadir leyenda
        ax_pie.legend(
            wedges, 
            pie_labels,
            title="Resultados",
            loc="center left",
            bbox_to_anchor=(0.85, 0.5),
            frameon=True,
            facecolor='#222244',
            edgecolor='gray',
            fontsize=9
        )
        
        ax_pie.axis('equal')
        ax_pie.set_title("Distribución Total por Resultado", color='white', fontsize=14)
        
        st.pyplot(fig_pie)
    
    with col2:
        # Evolución temporal por resultado
        st.markdown("### Tendencia temporal por resultado")
        
        # Crear tabla pivoteada para mostrar evolución
        tabla_evol = pivotado.copy()
        tabla_evol.index = labels
        
        # Renombrar columnas
        tabla_evol.columns = [resultados_nombres.get(c, f"Resultado {c}") for c in tabla_evol.columns]
        
        # Mostrar tabla
        st.dataframe(tabla_evol.style.background_gradient(
            cmap='viridis',
            axis=None,
            vmin=0,
            vmax=max([max(col) for col in pivotado.values.T])
        ).format("{:,.0f}"))
        
    # Análisis de la positividad por mes
    st.markdown("### Análisis de positividad mensual")
    
    if 1 in pivotado.columns and 2 in pivotado.columns:
        # Calcular tasa de positividad mensual (positivos / (positivos + negativos))
        positivos = pivotado[1]
        negativos = pivotado[2]
        total_pruebas = positivos + negativos
        
        # Evitar división por cero
        positividad = np.zeros(len(total_pruebas))
        for i, total in enumerate(total_pruebas):
            if total > 0:
                positividad[i] = (positivos.iloc[i] / total) * 100
        
        # Crear figura para la positividad
        fig_pos, ax_pos = plt.subplots(figsize=(12, 5), facecolor='#1e1e2f')
        fig_pos.patch.set_facecolor('#1e1e2f')
        
        # Gráfico de línea para positividad
        ax_pos.plot(
            range(1, 13),
            positividad,
            marker='o',
            markersize=8,
            linewidth=2,
            color="#e74c3c",
            alpha=0.9
        )
        
        # Personalización
        ax_pos.set_facecolor('#1e1e2f')
        ax_pos.set_title("Tasa de Positividad Mensual (Positivos/Total de Pruebas)", fontsize=14, color='white')
        ax_pos.set_xlabel("Mes", fontsize=12, color='white')
        ax_pos.set_ylabel("Porcentaje (%)", fontsize=12, color='white')
        ax_pos.set_xticks(range(1, 13))
        ax_pos.set_xticklabels(labels, color='white')
        ax_pos.tick_params(axis='y', colors='white')
        ax_pos.grid(axis='both', linestyle='--', alpha=0.3, color='gray')
        ax_pos.set_ylim(bottom=0, top=max(positividad) * 1.1)
        
        # Añadir etiquetas con porcentajes
        for i, porc in enumerate(positividad):
            if porc > 0:
                ax_pos.annotate(
                    f'{porc:.1f}%',
                    xy=(i+1, porc),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                    color='white',
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc='#222244', alpha=0.7, ec="gray")
                )
        
        # Mostrar gráfico
        st.pyplot(fig_pos)
        
        # Interpretación de resultados
        st.markdown("""
        <div style="background-color: #222244; padding: 15px; border-radius: 5px;">
            <h4 style="color: white; margin-top: 0;">Interpretación de la positividad</h4>
            <p style="color: white; margin: 5px 0;">
                La tasa de positividad es un indicador clave para monitorear la pandemia. Una tasa alta (>10%) puede 
                indicar que no se están realizando suficientes pruebas y que posiblemente hay muchos casos no detectados.
                Una tasa baja (<3%) sugiere que la mayoría de los casos están siendo capturados por el sistema de vigilancia.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No hay datos suficientes para calcular la positividad mensual.")

st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)
# Gráfico de Línea - Intubados por mes
# Gráfico de Línea - Pacientes Intubados por Mes con tema oscuro mejorado

# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Evolución Mensual de Pacientes Intubados</h3>
</div>
""", unsafe_allow_html=True)

# Asegurar que la fecha esté en formato datetime
df['FECHA_INGRESO'] = pd.to_datetime(df['FECHA_INGRESO'], errors='coerce')

# Filtrar datos válidos con fecha y estado de intubación
df_intubado = df[df['FECHA_INGRESO'].notna() & df['INTUBADO'].isin([1, 2, 97, 98, 99])].copy()

# Extraer mes
df_intubado['MES'] = df_intubado['FECHA_INGRESO'].dt.month

# Contar mensual
conteo_intubado = df_intubado.groupby(['MES', 'INTUBADO']).size().reset_index(name='PACIENTES')
pivot_intubado = conteo_intubado.pivot(index='MES', columns='INTUBADO', values='PACIENTES').fillna(0)

# Asegurar que todos los meses del 1 al 12 estén presentes
for mes in range(1, 13):
    if mes not in pivot_intubado.index:
        pivot_intubado.loc[mes] = [0] * len(pivot_intubado.columns)
pivot_intubado = pivot_intubado.sort_index()

# Etiquetas y colores mejorados
etiquetas = {
    1: "Intubado", 
    2: "No Intubado", 
    97: "No Aplica", 
    98: "Se Ignora", 
    99: "No Especificado"
}
labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# Colores personalizados
colores = {
    1: "#e74c3c",  # Rojo para intubados
    2: "#2ecc71",  # Verde para no intubados
    97: "#7f8c8d", # Gris para no aplica
    98: "#f39c12", # Naranja para se ignora
    99: "#3498db"  # Azul para no especificado
}

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig, ax = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Ordenar columnas para mejor visualización (primero intubados y no intubados)
orden_columnas = [col for col in [1, 2, 97, 98, 99] if col in pivot_intubado.columns]
columnas_ordenadas = pivot_intubado[orden_columnas]

# Crear gráficas de línea mejoradas
for col in orden_columnas:
    ax.plot(
        pivot_intubado.index, 
        pivot_intubado[col],
        marker='o',
        markersize=8,
        linewidth=3,
        color=colores.get(col, "#ffffff"),
        label=f"{etiquetas.get(col, f'Tipo {col}')}",
        alpha=0.9
    )

# Personalización avanzada del gráfico
ax.set_facecolor('#1e1e2f')
ax.set_title("Evolución Mensual de Pacientes por Estado de Intubación", fontsize=18, pad=20, color='white')
ax.set_xlabel("Mes", fontsize=14, color='white', labelpad=10)
ax.set_ylabel("Número de Pacientes", fontsize=14, color='white', labelpad=10)

# Mejorar diseño del eje X
ax.set_xticks(range(1, 13))
ax.set_xticklabels(labels, color='white', fontsize=12)

# Mejorar diseño del eje Y
ax.tick_params(axis='y', colors='white', labelsize=12)
import matplotlib.ticker as ticker
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{int(x):,}'))

# Añadir cuadrícula estilizada
ax.grid(axis='both', linestyle='--', alpha=0.3, color='gray')

# Mejorar la leyenda
legend = ax.legend(
    title="Estado de Intubación", 
    frameon=True, 
    facecolor='#222244', 
    edgecolor='gray',
    fontsize=12,
    loc='upper left'
)
legend.get_title().set_color('white')
legend.get_title().set_fontsize(13)
for text in legend.get_texts():
    text.set_color('white')

# Encontrar la serie con el valor máximo para evitar sobreposición de etiquetas
valores_max = {col: max(pivot_intubado[col]) for col in orden_columnas}
col_max = max(valores_max, key=valores_max.get)

# Añadir anotaciones para valores importantes
for col in orden_columnas:
    for mes, valor in enumerate(pivot_intubado[col], 1):
        if valor > max(pivot_intubado[col]) * 0.3:  # Solo mostrar valores significativos (30% del máximo)
            # Ajustar la posición vertical para evitar solapamiento
            offset_y = 10 if col == col_max else -20
            
            ax.annotate(
                f'{int(valor):,}', 
                xy=(mes, valor),
                xytext=(0, offset_y),
                textcoords='offset points',
                ha='center',
                va='bottom' if offset_y > 0 else 'top',
                color='white',
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", fc='#222244', alpha=0.7, ec="gray")
            )

# Añadir línea de contorno al gráfico
for spine in ax.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Ajustar el diseño
plt.tight_layout()

# Mostrar en Streamlit
st.pyplot(fig)

# Añadir análisis adicional
with st.expander("Análisis detallado de pacientes intubados"):
    # Calcular estadísticas generales
    if 1 in pivot_intubado.columns and 2 in pivot_intubado.columns:
        total_intubados = pivot_intubado[1].sum()
        total_no_intubados = pivot_intubado[2].sum()
        total_pacientes_registrados = total_intubados + total_no_intubados
        
        # Encontrar el mes con más intubados
        mes_max_intubados = pivot_intubado[1].idxmax()
        max_intubados = pivot_intubado[1].max()
        
        # Encontrar el mes con la mayor proporción de intubados vs no intubados
        proporciones = pivot_intubado[1] / (pivot_intubado[1] + pivot_intubado[2])
        proporciones = proporciones.fillna(0)
        mes_max_proporcion = proporciones.idxmax()
        max_proporcion = proporciones.max()
        
        # Mostrar estadísticas
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
                <h4 style="color: white; margin-top: 0;">Estadísticas generales</h4>
                <p style="color: white; margin: 0;">Total de pacientes <span style="color: {colores[1]};">Intubados</span>: {total_intubados:,} ({total_intubados/total_pacientes_registrados*100:.1f}%)</p>
                <p style="color: white; margin: 0;">Total de pacientes <span style="color: {colores[2]};">No Intubados</span>: {total_no_intubados:,} ({total_no_intubados/total_pacientes_registrados*100:.1f}%)</p>
                <p style="color: white; margin: 0;">Mes con más pacientes intubados: <strong>{labels[mes_max_intubados-1]}</strong> ({max_intubados:,} pacientes)</p>
                <p style="color: white; margin: 0;">Mes con mayor proporción de intubación: <strong>{labels[mes_max_proporcion-1]}</strong> ({max_proporcion*100:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Crear un gráfico de pastel que muestre la proporción global
            fig_pie, ax_pie = plt.subplots(figsize=(5, 5), facecolor='#1e1e2f')
            fig_pie.patch.set_facecolor('#1e1e2f')
            
            ax_pie.pie(
                [total_intubados, total_no_intubados],
                labels=["Intubados", "No Intubados"],
                autopct='%1.1f%%',
                startangle=90,
                colors=[colores[1], colores[2]],
                wedgeprops=dict(width=0.5, edgecolor='white', linewidth=0.5)  # Para hacerlo tipo donut
            )
            
            # Añadir círculo central para efecto donut
            centre_circle = plt.Circle((0, 0), 0.25, fc='#1e1e2f')
            ax_pie.add_patch(centre_circle)
            
            ax_pie.axis('equal')
            ax_pie.set_title("Distribución de Pacientes por Estado de Intubación", color='white', fontsize=14)
            
            # Mejorar textos del pie chart
            for text in ax_pie.texts:
                text.set_color('white')
            
            st.pyplot(fig_pie)
        
        # Tendencia mensual de proporción de intubados
        st.markdown("### Tendencia mensual de la proporción de pacientes intubados")
        
        # Calcular la proporción de intubados respecto al total de cada mes
        total_mensual = pivot_intubado[1] + pivot_intubado[2]
        proporcion_mensual = (pivot_intubado[1] / total_mensual).fillna(0) * 100
        
        # Crear figura para la proporción mensual
        fig_prop, ax_prop = plt.subplots(figsize=(12, 5), facecolor='#1e1e2f')
        fig_prop.patch.set_facecolor('#1e1e2f')
        
        # Gráfico de línea para la proporción mensual
        ax_prop.plot(
            proporcion_mensual.index,
            proporcion_mensual.values,
            marker='o',
            markersize=8,
            linewidth=3,
            color="#e74c3c",
            alpha=0.9
        )
        
        # Añadir un área sombreada bajo la línea para destacar
        ax_prop.fill_between(
            proporcion_mensual.index,
            proporcion_mensual.values,
            color="#e74c3c", 
            alpha=0.15
        )
        
        # Personalización
        ax_prop.set_facecolor('#1e1e2f')
        ax_prop.set_title("Porcentaje de Pacientes Intubados por Mes", fontsize=14, color='white')
        ax_prop.set_xlabel("Mes", fontsize=12, color='white')
        ax_prop.set_ylabel("Porcentaje de Intubados (%)", fontsize=12, color='white')
        ax_prop.set_xticks(range(1, 13))
        ax_prop.set_xticklabels(labels, color='white')
        ax_prop.tick_params(axis='y', colors='white')
        ax_prop.grid(axis='both', linestyle='--', alpha=0.3, color='gray')
        
        # Añadir etiquetas con porcentajes
        for mes, porcentaje in enumerate(proporcion_mensual.values, 1):
            if not np.isnan(porcentaje) and porcentaje > 0:
                ax_prop.annotate(
                    f'{porcentaje:.1f}%',
                    xy=(mes, porcentaje),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                    color='white',
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc='#222244', alpha=0.7, ec="gray")
                )
        
        # Añadir líneas de referencia horizontales para mejor contexto
        mean_prop = proporcion_mensual.mean()
        ax_prop.axhline(y=mean_prop, color='white', linestyle='--', alpha=0.5)
        ax_prop.annotate(
            f'Media: {mean_prop:.1f}%', 
            xy=(12, mean_prop),
            xytext=(8, 0), 
            textcoords="offset points",
            color='white',
            fontsize=9,
            va='center'
        )
        
        # Mostrar gráfico de proporción
        st.pyplot(fig_prop)
        
        # Tabla de datos mensuales
        st.markdown("### Datos detallados por mes")
        
        # Preparar tabla para mostrar
        tabla_meses = pd.DataFrame({
            'Mes': labels,
            'Intubados': pivot_intubado[1].values,
            'No Intubados': pivot_intubado[2].values,
            'Total': total_mensual.values,
            '% Intubados': proporcion_mensual.values
        })
        
        # Formatear valores numéricos
        for col in ['Intubados', 'No Intubados', 'Total']:
            tabla_meses[col] = tabla_meses[col].astype(int).apply(lambda x: f"{x:,}")
        tabla_meses['% Intubados'] = tabla_meses['% Intubados'].apply(lambda x: f"{x:.1f}%")
        
        # Mostrar tabla
        st.table(tabla_meses)
    else:
        st.warning("No hay suficientes datos para analizar la intubación por mes.")
#--------------------------------------------
st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

# === Gráfico de Línea - Intubados por mes (empezando en 0 en enero y febrero) ===
# Gráfico de Línea - Pacientes Intubados por Mes (tema oscuro)

# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Evolución Mensual de Pacientes Intubados</h3>
</div>
""", unsafe_allow_html=True)

# Asegurar que la fecha esté en formato datetime
df['FECHA_INGRESO'] = pd.to_datetime(df['FECHA_INGRESO'], errors='coerce')

# Filtrar datos válidos con fecha y estado de intubación 1 o 2
df_intubado = df[df['FECHA_INGRESO'].notna() & df['INTUBADO'].isin([1, 2])].copy()

# Extraer mes
df_intubado['MES'] = df_intubado['FECHA_INGRESO'].dt.month

# Conteo mensual real desde marzo (mes 3) en adelante
conteo_real = df_intubado[df_intubado['MES'] >= 3] \
    .groupby(['MES', 'INTUBADO']) \
    .size().reset_index(name='PACIENTES')

# Crear DataFrame base con ceros para enero (1) y febrero (2)
meses_cero = pd.DataFrame([
    {"MES": mes, "INTUBADO": estado, "PACIENTES": 0}
    for mes in [1, 2]
    for estado in [1, 2]
])

# Unir conteos
conteo_completo = pd.concat([meses_cero, conteo_real], ignore_index=True)

# Pivotear
pivot_intubado = conteo_completo.pivot(index='MES', columns='INTUBADO', values='PACIENTES').fillna(0)

# Asegurar que todos los meses del 1 al 12 estén presentes
for mes in range(1, 13):
    if mes not in pivot_intubado.index:
        pivot_intubado.loc[mes] = [0, 0]
pivot_intubado = pivot_intubado.sort_index()

# Etiquetas de los ejes
etiquetas = {1: "Sí", 2: "No"}
labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig, ax = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Colores personalizados para las líneas
color_intubado_si = "#e74c3c"  # Rojo para intubados
color_intubado_no = "#2ecc71"  # Verde para no intubados

# Colores por tipo de intubación
colores = {1: color_intubado_si, 2: color_intubado_no}

# Crear gráficas de línea mejoradas
for col in pivot_intubado.columns:
    ax.plot(
        pivot_intubado.index, 
        pivot_intubado[col],
        marker='o',
        markersize=8,
        linewidth=3,
        color=colores.get(col, "#ffffff"),
        label=f"Intubado: {etiquetas.get(col, col)}",
        alpha=0.9
    )

# Personalización avanzada del gráfico
ax.set_facecolor('#1e1e2f')
ax.set_title("Evolución Mensual de Pacientes Intubados", fontsize=18, pad=20, color='white')
ax.set_xlabel("Mes", fontsize=14, color='white', labelpad=10)
ax.set_ylabel("Número de Pacientes", fontsize=14, color='white', labelpad=10)

# Mejorar diseño del eje X
ax.set_xticks(range(1, 13))
ax.set_xticklabels(labels, color='white', fontsize=12)

# Mejorar diseño del eje Y
ax.tick_params(axis='y', colors='white', labelsize=12)

# Añadir cuadrícula estilizada
ax.grid(axis='both', linestyle='--', alpha=0.3, color='gray')

# Mejorar la leyenda
legend = ax.legend(
    title="Estado de Intubación", 
    frameon=True, 
    facecolor='#222244', 
    edgecolor='gray',
    fontsize=12,
    loc='upper left'
)
legend.get_title().set_color('white')
legend.get_title().set_fontsize(13)
for text in legend.get_texts():
    text.set_color('white')

# Añadir anotaciones para valores en los puntos
for col in pivot_intubado.columns:
    for mes, valor in enumerate(pivot_intubado[col], 1):
        if valor > 0:
            ax.annotate(
                f'{int(valor):,}', 
                xy=(mes, valor),
                xytext=(0, 10 if col == 1 else -20),  # Ajustar posición para evitar solapamiento
                textcoords='offset points',
                ha='center',
                va='bottom' if col == 1 else 'top',
                color='white',
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", fc='#222244', alpha=0.7, ec="gray")
            )

# Añadir línea de contorno al gráfico
for spine in ax.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Ajustar el diseño
plt.tight_layout()

# Mostrar en Streamlit
st.pyplot(fig)

# Añadir análisis adicional
with st.expander("Detalles del análisis de pacientes intubados"):
    # Calcular estadísticas interesantes
    total_intubados = pivot_intubado[1].sum()
    total_no_intubados = pivot_intubado[2].sum()
    total_pacientes = total_intubados + total_no_intubados
    
    # Encontrar el mes con más intubados
    mes_max_intubados = pivot_intubado[1].idxmax()
    max_intubados = pivot_intubado[1].max()
    
    # Encontrar el mes con la mayor proporción de intubados vs no intubados
    proporciones = pivot_intubado[1] / (pivot_intubado[1] + pivot_intubado[2])
    proporciones = proporciones.fillna(0)
    mes_max_proporcion = proporciones.idxmax()
    max_proporcion = proporciones.max()
    
    # Mostrar estadísticas
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
            <p style="color: white; margin: 0;">Total de pacientes <span style="color: {color_intubado_si};">Intubados</span>: {total_intubados:,} ({total_intubados/total_pacientes*100:.1f}%)</p>
            <p style="color: white; margin: 0;">Total de pacientes <span style="color: {color_intubado_no};">No Intubados</span>: {total_no_intubados:,} ({total_no_intubados/total_pacientes*100:.1f}%)</p>
            <p style="color: white; margin: 0;">Mes con más pacientes intubados: {labels[mes_max_intubados-1]} ({max_intubados:,} pacientes)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Crear un gráfico de pastel que muestre la proporción global
        fig_pie, ax_pie = plt.subplots(figsize=(5, 5), facecolor='#1e1e2f')
        fig_pie.patch.set_facecolor('#1e1e2f')
        
        ax_pie.pie(
            [total_intubados, total_no_intubados],
            labels=["Intubados", "No Intubados"],
            autopct='%1.1f%%',
            startangle=90,
            colors=[color_intubado_si, color_intubado_no],
            wedgeprops=dict(width=0.5)  # Para hacerlo tipo donut
        )
        ax_pie.axis('equal')
        ax_pie.set_title("Distribución de Pacientes por Estado de Intubación", color='white')
        
        # Mejorar leyenda del pie chart
        for text in ax_pie.texts:
            text.set_color('white')
        
        st.pyplot(fig_pie)
    
    # Tendencia mensual de proporción de intubados
    st.markdown("### Tendencia mensual de la proporción de pacientes intubados")
    
    # Calcular la proporción de intubados respecto al total de cada mes
    total_mensual = pivot_intubado[1] + pivot_intubado[2]
    proporcion_mensual = (pivot_intubado[1] / total_mensual).fillna(0) * 100
    
    # Crear figura para la proporción mensual
    fig_prop, ax_prop = plt.subplots(figsize=(12, 5), facecolor='#1e1e2f')
    fig_prop.patch.set_facecolor('#1e1e2f')
    
    # Gráfico de línea para la proporción mensual
    ax_prop.plot(
        proporcion_mensual.index,
        proporcion_mensual.values,
        marker='o',
        markersize=8,
        linewidth=3,
        color="#e74c3c",
        alpha=0.9
    )
    
    # Personalización
    ax_prop.set_facecolor('#1e1e2f')
    ax_prop.set_title("Porcentaje de Pacientes Intubados por Mes", fontsize=14, color='white')
    ax_prop.set_xlabel("Mes", fontsize=12, color='white')
    ax_prop.set_ylabel("Porcentaje de Intubados (%)", fontsize=12, color='white')
    ax_prop.set_xticks(range(1, 13))
    ax_prop.set_xticklabels(labels, color='white')
    ax_prop.tick_params(axis='y', colors='white')
    ax_prop.grid(axis='both', linestyle='--', alpha=0.3, color='gray')
    
    # Añadir etiquetas con porcentajes
    for mes, porcentaje in enumerate(proporcion_mensual.values, 1):
        if not np.isnan(porcentaje) and porcentaje > 0:
            ax_prop.annotate(
                f'{porcentaje:.1f}%',
                xy=(mes, porcentaje),
                xytext=(0, 10),
                textcoords='offset points',
                ha='center',
                va='bottom',
                color='white',
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", fc='#222244', alpha=0.7, ec="gray")
            )
    
    # Mostrar gráfico de proporción
    st.pyplot(fig_prop)

# --- Gráfica de pastel: Porcentaje de enfermedades en casos confirmados ---


# --- Separador visual ---
st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

# --- Gráfica de pastel: Porcentaje de enfermedades en casos confirmados ---
# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Comorbilidades en Casos Confirmados</h3>
</div>
""", unsafe_allow_html=True)

# Lista de columnas de enfermedades
columnas_enfermedades = [
    "DIABETES", "HIPERTENSION", "OBESIDAD", "RENAL_CRONICA", "CARDIOVASCULAR",
    "EPOC", "ASMA", "INMUSUPR", "TABAQUISMO", "OTRA_COM"
]

# Diccionario para nombres más legibles
nombres_legibles = {
    "DIABETES": "Diabetes",
    "HIPERTENSION": "Hipertensión",
    "OBESIDAD": "Obesidad",
    "RENAL_CRONICA": "Enfermedad Renal",
    "CARDIOVASCULAR": "Enfermedad Cardiovascular",
    "EPOC": "EPOC",
    "ASMA": "Asma",
    "INMUSUPR": "Inmunosupresión",
    "TABAQUISMO": "Tabaquismo",
    "OTRA_COM": "Otras comorbilidades"
}

# Contar casos donde el valor es 1 (tiene la enfermedad)
conteo_comorbilidades = {}
for col in columnas_enfermedades:
    if col in df_confirmados.columns:
        total = df_confirmados[df_confirmados[col] == 1].shape[0]
        if total > 0:
            conteo_comorbilidades[nombres_legibles.get(col, col)] = total

# Calcular porcentajes
suma_total = sum(conteo_comorbilidades.values())
porcentajes = {k: round((v / suma_total) * 100, 1) for k, v in conteo_comorbilidades.items()}

# Ordenar por porcentaje descendente
porcentajes = dict(sorted(porcentajes.items(), key=lambda item: item[1], reverse=True))

# Paleta de colores atractiva para tema oscuro
colors = [
    "#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#34495e", "#7f8c8d", "#d35400"
]

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig_pie, ax_pie = plt.subplots(figsize=(10, 8), facecolor='#1e1e2f')
fig_pie.patch.set_facecolor('#1e1e2f')

# Crear gráfico de pastel mejorado
wedges, texts, autotexts = ax_pie.pie(
    porcentajes.values(),
    labels=None,  # Quitamos las etiquetas para usar una leyenda separada
    autopct='%1.1f%%',
    startangle=90,
    wedgeprops=dict(width=0.5, edgecolor='white', linewidth=0.5),  # Donut con borde blanco
    pctdistance=0.95,  # Mover los porcentajes más hacia afuera
    colors=colors[:len(porcentajes)]
)

# Personalizar textos de porcentajes
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(7)
    autotext.set_weight('bold')

# Añadir un círculo en el centro para un efecto donut más pronunciado
centre_circle = plt.Circle((0, 0), 0.35, fc='#1e1e2f')
ax_pie.add_patch(centre_circle)

# Añadir título dentro del círculo central
ax_pie.annotate(
    "Comorbilidades",
    xy=(0, 0),
    ha='center',
    va='center',
    fontsize=14,
    fontweight='bold',
    color='white'
)

# Ajustar la leyenda para mejor visibilidad
ax_pie.legend(
    wedges,
    [f"{k} ({v}%)" for k, v in porcentajes.items()],
    title="Comorbilidades",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.5, 1),
    frameon=True,
    facecolor='#222244',
    edgecolor='gray',
    fontsize=10
)

# Personalizar más el gráfico
ax_pie.set_title("Distribución de Comorbilidades en Casos Confirmados", fontsize=16, pad=20, color='white')
ax_pie.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

# Información adicional
total_casos = len(df_confirmados)
casos_con_comorbilidad = sum(conteo_comorbilidades.values())
porc_con_comorbilidad = round((casos_con_comorbilidad / total_casos) * 100, 1)

# Pie de gráfico con información
fig_pie.text(
    0.5, 0.02,
    f"Total de casos analizados: {total_casos:,} | Casos con al menos una comorbilidad: {porc_con_comorbilidad}%",
    ha='center',
    color='white',
    fontsize=10,
    alpha=0.7
)

# Mostrar gráfico
st.pyplot(fig_pie)

# Añadir un expander con análisis detallado
with st.expander("Análisis detallado de comorbilidades"):
    # Datos de resumen
    st.markdown(f"""
    <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
        <p style="color: white; margin: 0;">Total de casos confirmados: <strong>{total_casos:,}</strong></p>
        <p style="color: white; margin: 0;">Casos con al menos una comorbilidad: <strong>{casos_con_comorbilidad:,}</strong> ({porc_con_comorbilidad}%)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabla comparativa
    st.markdown("### Tabla comparativa de comorbilidades")
    
    # Crear una tabla con todos los datos
    tabla_data = []
    for nombre, conteo in conteo_comorbilidades.items():
        porcentaje = (conteo / total_casos) * 100
        tabla_data.append({
            "Comorbilidad": nombre,
            "Casos": f"{conteo:,}",
            "% sobre confirmados": f"{porcentaje:.1f}%",
            "% sobre comorbilidades": f"{porcentajes[nombre]:.1f}%"
        })
    
    tabla_df = pd.DataFrame(tabla_data)
    st.table(tabla_df)

# --- Separador visual ---
st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

# --- Distribución por Edad en Rangos (Histograma) ---
# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución de Casos por Rango de Edad</h3>
</div>
""", unsafe_allow_html=True)

# Filtrar edades válidas
df_edad = df[df['EDAD'].notna() & (df['EDAD'] >= 0)]

# Definir rangos y etiquetas
bins = list(range(0, 100, 5)) + [150]
labels = [f"{i}-{i+4}" for i in range(0, 95, 5)] + ["95+"]

# Agrupar por rangos
df_edad['RANGO_EDAD'] = pd.cut(df_edad['EDAD'], bins=bins, labels=labels, right=False)

# Contar frecuencias por rango
conteo_rangos = df_edad['RANGO_EDAD'].value_counts().sort_index()

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig, ax = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Colores con gradiente para más atractivo visual
gradient_colors = plt.cm.viridis(np.linspace(0, 0.8, len(conteo_rangos)))

# Crear gráfico de barras mejorado
bars = ax.bar(
    range(len(conteo_rangos)),
    conteo_rangos.values,
    color=gradient_colors,
    edgecolor='white',
    linewidth=0.5,
    alpha=0.8
)

# Personalizar el gráfico
ax.set_facecolor('#1e1e2f')
ax.set_title("Distribución de Casos por Rango de Edad", fontsize=16, pad=20, color='white')
ax.set_xlabel("Rango de Edad", fontsize=12, color='white', labelpad=10)
ax.set_ylabel("Número de Casos", fontsize=12, color='white', labelpad=10)

# Mejorar el diseño del eje X
ax.set_xticks(range(len(conteo_rangos)))
ax.set_xticklabels(labels, rotation=45, ha='right', color='white', fontsize=10)

# Mejorar el diseño del eje Y
ax.tick_params(axis='y', colors='white', labelsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')

# Añadir valores en las barras para las más significativas
umbral = max(conteo_rangos) * 0.05  # Solo mostrar valores para barras con > 5% del máximo

for i, v in enumerate(conteo_rangos.values):
    if v > umbral:
        ax.text(
            i, 
            v + (max(conteo_rangos) * 0.01),  # Pequeño desplazamiento hacia arriba
            f'{int(v):,}', 
            ha='center', 
            va='bottom',
            color='white',
            fontsize=9,
            rotation=0,
            bbox=dict(boxstyle="round,pad=0.3", fc='#222244', alpha=0.7, ec="gray")
        )

# Añadir línea de contorno al gráfico
for spine in ax.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Ajustar el diseño
plt.tight_layout()

# Mostrar gráfico
st.pyplot(fig)

# Añadir estadísticas de interés
col1, col2, col3 = st.columns(3)

with col1:
    # Encontrar el rango de edad con más casos
    rango_max = conteo_rangos.idxmax()
    max_casos = conteo_rangos.max()
    st.metric(
        "Rango de edad más frecuente", 
        f"{rango_max}", 
        f"{max_casos:,} casos"
    )
    
with col2:
    # Calcular edad promedio (usamos el punto medio de cada rango)
    rangos_dict = {}
    for i, label in enumerate(labels):
        if "-" in label:
            inicio = int(label.split("-")[0])
            fin = int(label.split("-")[1])
            rangos_dict[label] = (inicio + fin) / 2
        else:  # Para "95+"
            rangos_dict[label] = 97.5
    
    # Calcular promedio ponderado
    total_casos = conteo_rangos.sum()
    suma_ponderada = sum(rangos_dict[rango] * casos for rango, casos in conteo_rangos.items())
    edad_promedio = suma_ponderada / total_casos if total_casos > 0 else 0
    
    st.metric(
        "Edad promedio estimada", 
        f"{edad_promedio:.1f} años", 
        help="Calculado usando el punto medio de cada rango de edad"
    )
    
with col3:
    # Calcular mediana (aproximada por rangos)
    casos_acumulados = 0
    mediana_rango = labels[0]
    mitad = total_casos / 2
    
    for rango, casos in conteo_rangos.items():
        casos_acumulados += casos
        if casos_acumulados >= mitad:
            mediana_rango = rango
            break
            
    st.metric(
        "Rango de edad mediano", 
        f"{mediana_rango}", 
        help="Rango donde se alcanza el 50% acumulado de casos"
    )

# Añadir un expander con análisis detallado
with st.expander("Análisis detallado de la distribución por edad"):
    # Calcular porcentajes por grupo de edad amplio
    jovenes = sum(conteo_rangos[rango] for rango in conteo_rangos.index if rangos_dict[rango] < 30)
    adultos = sum(conteo_rangos[rango] for rango in conteo_rangos.index if 30 <= rangos_dict[rango] < 60)
    mayores = sum(conteo_rangos[rango] for rango in conteo_rangos.index if rangos_dict[rango] >= 60)
    
    porc_jovenes = (jovenes / total_casos) * 100
    porc_adultos = (adultos / total_casos) * 100
    porc_mayores = (mayores / total_casos) * 100
    
    st.markdown(f"""
    <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
        <p style="color: white; margin: 0;">Jóvenes (0-29 años): <strong>{jovenes:,}</strong> casos ({porc_jovenes:.1f}%)</p>
        <p style="color: white; margin: 0;">Adultos (30-59 años): <strong>{adultos:,}</strong> casos ({porc_adultos:.1f}%)</p>
        <p style="color: white; margin: 0;">Mayores (60+ años): <strong>{mayores:,}</strong> casos ({porc_mayores:.1f}%)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Gráfico de pastel por grupos de edad amplios
    fig_grupos, ax_grupos = plt.subplots(figsize=(8, 5), facecolor='#1e1e2f')
    fig_grupos.patch.set_facecolor('#1e1e2f')
    
    datos_grupos = [jovenes, adultos, mayores]
    labels_grupos = ['Jóvenes (0-29)', 'Adultos (30-59)', 'Mayores (60+)']
    colores_grupos = ['#3498db', '#2ecc71', '#e74c3c']
    
    wedges, texts, autotexts = ax_grupos.pie(
        datos_grupos,
        labels=labels_grupos,
        autopct='%1.1f%%',
        startangle=90,
        colors=colores_grupos,
        explode=[0, 0.05, 0.1],  # Separar un poco el grupo de mayores
        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=0.5)
    )
    
    # Personalizar textos
    for text, autotext in zip(texts, autotexts):
        text.set_color('white')
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax_grupos.axis('equal')
    ax_grupos.set_title("Distribución por Grupos de Edad", color='white', fontsize=14)
    
    st.pyplot(fig_grupos)

# --- Gráfico de barras horizontales: comorbilidades en confirmados o fallecidos ---

st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

# --- Gráfico de barras horizontales: comorbilidades en confirmados o fallecidos ---

# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Comorbilidades Más Frecuentes</h3>
</div>
""", unsafe_allow_html=True)

# Selector de tipo de análisis con estilo mejorado
tipo_comparacion = st.radio(
    "Selecciona el grupo a analizar:",
    ("Casos Confirmados", "Casos Fallecidos"),
    horizontal=True,
    key="comorbilidades_tipo"
)

# Filtrar DataFrame según la selección
if tipo_comparacion == "Casos Confirmados":
    df_comorbilidad = df[df['CLASIFICACION_FINAL'] == 1].copy()
    color_base = "#3498db"  # Azul para confirmados
else:
    df_comorbilidad = df[
        (df['CLASIFICACION_FINAL'] == 1) &
        (df['FECHA_DEF'].notna()) &
        (df['FECHA_DEF'] != '9999-99-99')
    ].copy()
    color_base = "#e74c3c"  # Rojo para fallecidos

# Columnas de comorbilidades
columnas_comorb = [
    "DIABETES", "HIPERTENSION", "OBESIDAD", "EPOC", "ASMA",
    "CARDIOVASCULAR", "RENAL_CRONICA", "TABAQUISMO", "INMUSUPR", "OTRA_COM"
]

# Diccionario para nombres más legibles
nombres_legibles = {
    "DIABETES": "Diabetes",
    "HIPERTENSION": "Hipertensión",
    "OBESIDAD": "Obesidad",
    "RENAL_CRONICA": "Enfermedad Renal",
    "CARDIOVASCULAR": "Enfermedad Cardiovascular",
    "EPOC": "EPOC",
    "ASMA": "Asma",
    "INMUSUPR": "Inmunosupresión",
    "TABAQUISMO": "Tabaquismo",
    "OTRA_COM": "Otras comorbilidades"
}

# Calcular frecuencias (solo donde el valor es 1)
frecuencias = {
    nombres_legibles.get(col, col): df_comorbilidad[df_comorbilidad[col] == 1].shape[0]
    for col in columnas_comorb if col in df_comorbilidad.columns
}

# Calcular porcentajes sobre el total de pacientes
total_pacientes = len(df_comorbilidad)
porcentajes = {k: (v / total_pacientes) * 100 for k, v in frecuencias.items()}

# Convertir a DataFrame y ordenar
df_comorb_plot = pd.DataFrame({
    'Pacientes': frecuencias,
    'Porcentaje': porcentajes
})
df_comorb_plot = df_comorb_plot.sort_values(by='Pacientes', ascending=True)

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig, ax = plt.subplots(figsize=(12, 8), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Crear gráfico de barras horizontales con gradiente de color
cmap = plt.cm.get_cmap('YlOrRd' if tipo_comparacion == "Casos Fallecidos" else 'YlGnBu')
colors = cmap(np.linspace(0.3, 1.0, len(df_comorb_plot)))

# Crear barras con gradiente y borde blanco
bars = ax.barh(
    df_comorb_plot.index, 
    df_comorb_plot['Pacientes'], 
    color=colors, 
    edgecolor='white',
    linewidth=0.5,
    alpha=0.8
)

# Personalización avanzada del gráfico
ax.set_facecolor('#1e1e2f')
ax.set_title(f"Comorbilidades en {tipo_comparacion}", fontsize=16, pad=20, color='white')
ax.set_xlabel("Número de Pacientes", fontsize=12, color='white')
ax.set_ylabel("Comorbilidad", fontsize=12, color='white')

# Añadir valores y porcentajes al final de cada barra
for i, bar in enumerate(bars):
    width = bar.get_width()
    label_text = f"{int(width):,} ({df_comorb_plot['Porcentaje'].iloc[i]:.1f}%)"
    ax.text(
        width + (max(df_comorb_plot['Pacientes']) * 0.02),  # Pequeño desplazamiento a la derecha
        bar.get_y() + bar.get_height()/2,
        label_text,
        va='center',
        ha='left',
        color='white',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", fc='#222244', alpha=0.7, ec="gray")
    )

# Mejorar el diseño de los ejes
ax.tick_params(axis='both', colors='white')
ax.grid(axis='x', linestyle='--', alpha=0.3, color='gray')

# Añadir línea de contorno al gráfico
for spine in ax.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Ajustar el diseño para evitar recorte
plt.tight_layout()

# Mostrar gráfico
st.pyplot(fig)

# Añadir análisis adicional
with st.expander(f"Análisis detallado de comorbilidades en {tipo_comparacion.lower()}"):
    col1, col2 = st.columns(2)
    
    with col1:
        # Tabla de datos
        st.markdown("### Datos numéricos")
        
        # Ordenar por porcentaje para la tabla
        tabla_data = df_comorb_plot.reset_index()
        tabla_data.columns = ["Comorbilidad", "Casos", "Porcentaje"]
        tabla_data = tabla_data.sort_values(by="Porcentaje", ascending=False)
        tabla_data["Porcentaje"] = tabla_data["Porcentaje"].apply(lambda x: f"{x:.1f}%")
        tabla_data["Casos"] = tabla_data["Casos"].apply(lambda x: f"{int(x):,}")
        
        st.table(tabla_data)
        
    with col2:
        # Métricas relevantes
        st.markdown("### Estadísticas principales")
        
        # Contar pacientes con al menos una comorbilidad
        tiene_alguna = 0
        for col in columnas_comorb:
            if col in df_comorbilidad.columns:
                tiene_alguna += (df_comorbilidad[col] == 1).any(axis=0)
                
        # Calcular porcentaje
        porc_con_comorb = (tiene_alguna / total_pacientes) * 100 if total_pacientes > 0 else 0
        
        # Mostrar métrica
        st.metric(
            "Pacientes con al menos una comorbilidad", 
            f"{porc_con_comorb:.1f}%",
            help=f"Del total de {total_pacientes:,} {tipo_comparacion.lower()}"
        )
        
        # Encontrar comorbilidad más común
        top_comorb = df_comorb_plot['Pacientes'].idxmax()
        top_valor = df_comorb_plot['Pacientes'].max()
        top_porc = df_comorb_plot['Porcentaje'].max()
        
        st.metric(
            "Comorbilidad más frecuente", 
            f"{top_comorb}",
            f"{int(top_valor):,} casos ({top_porc:.1f}%)"
        )

# --- Separador visual ---
st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)

# --- Gráfico de barras agrupadas por mes: CLASIFICACION_FINAL ---
# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución de Casos Sospechosos por Mes</h3>
</div>
""", unsafe_allow_html=True)

# Convertir fecha y filtrar clasificaciones válidas
df_sospechosos = df.copy()
df_sospechosos['FECHA_INGRESO'] = pd.to_datetime(df_sospechosos['FECHA_INGRESO'], errors='coerce')
df_sospechosos = df_sospechosos[df_sospechosos['CLASIFICACION_FINAL'].isin([3, 6, 7])]
df_sospechosos = df_sospechosos[df_sospechosos['FECHA_INGRESO'].notna()].copy()

# Extraer mes
df_sospechosos['MES'] = df_sospechosos['FECHA_INGRESO'].dt.month

# Conteo real desde abril en adelante
conteo_real = df_sospechosos[df_sospechosos['MES'] >= 4] \
    .groupby(['MES', 'CLASIFICACION_FINAL']) \
    .size().reset_index(name='PACIENTES')

# Agregar ceros para enero-marzo
meses_cero = pd.DataFrame([
    {'MES': mes, 'CLASIFICACION_FINAL': clasif, 'PACIENTES': 0}
    for mes in [1, 2, 3]
    for clasif in [3, 6, 7]
])

# Combinar conteos
conteo_completo = pd.concat([meses_cero, conteo_real], ignore_index=True)
pivotado = conteo_completo.pivot(index='MES', columns='CLASIFICACION_FINAL', values='PACIENTES').fillna(0)

# Asegurar que todos los meses del 1 al 12 estén presentes
for mes in range(1, 13):
    if mes not in pivotado.index:
        pivotado.loc[mes] = [0, 0, 0]
pivotado = pivotado.sort_index()

# Etiquetas y colores mejorados
labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
colores_clasif = {
    3: "#f39c12",  # Naranja
    6: "#3498db",  # Azul
    7: "#2ecc71"   # Verde
}
nombres_clasif = {
    3: "Sospechoso",
    6: "Probable", 
    7: "Negativo"
}

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig, ax = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Crear barras agrupadas
x = np.arange(len(labels))
width = 0.25  # ancho de cada barra
offset = 0

# Dibujar cada grupo de barras
for i, clasif in enumerate(pivotado.columns):
    bars = ax.bar(
        x + offset, 
        pivotado[clasif], 
        width, 
        label=nombres_clasif.get(clasif, f"Clase {clasif}"),
        color=colores_clasif.get(clasif, "#ffffff"),
        edgecolor='white',
        linewidth=0.5,
        alpha=0.8
    )
    
    # Añadir etiquetas a barras significativas
    umbral = max(pivotado[clasif]) * 0.1  # Solo mostrar valores para barras con > 10% del máximo
    for j, bar in enumerate(bars):
        height = bar.get_height()
        if height > umbral:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 5,
                f'{int(height):,}',
                ha='center', va='bottom',
                color='white',
                fontsize=8,
                rotation=0,
                bbox=dict(boxstyle="round,pad=0.2", fc='#222244', alpha=0.7, ec="gray")
            )
    
    # Actualizar offset para la siguiente serie
    offset += width

# Personalización avanzada del gráfico
ax.set_facecolor('#1e1e2f')
ax.set_title("Evolución Mensual de Casos por Tipo de Clasificación", fontsize=16, pad=20, color='white')
ax.set_xlabel("Mes", fontsize=12, color='white')
ax.set_ylabel("Número de Pacientes", fontsize=12, color='white')

# Configurar eje X
ax.set_xticks(x + width)
ax.set_xticklabels(labels, color='white')

# Configurar eje Y
ax.tick_params(axis='y', colors='white')
ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')

# Mejorar la leyenda
legend = ax.legend(
    title="Clasificación Final",
    frameon=True,
    facecolor='#222244',
    edgecolor='gray',
    fontsize=10,
    loc='upper left'
)
legend.get_title().set_color('white')
for text in legend.get_texts():
    text.set_color('white')

# Añadir línea de contorno al gráfico
for spine in ax.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Ajustar el diseño
plt.tight_layout()

# Mostrar gráfico
st.pyplot(fig)

# Añadir análisis adicional
with st.expander("Análisis detallado por clasificación"):
    # Calcular totales por clasificación
    totales_por_clasif = pivotado.sum()
    
    # Encontrar mes con más casos para cada clasificación
    meses_pico = {}
    for clasif in pivotado.columns:
        mes_pico = pivotado[clasif].idxmax()
        valor_pico = pivotado[clasif].max()
        meses_pico[clasif] = (mes_pico, valor_pico)
    
    # Mostrar estadísticas
    st.markdown("""
    <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
        <h4 style="color: white; margin-top: 0;">Totales por clasificación</h4>
    """, unsafe_allow_html=True)
    
    for clasif in pivotado.columns:
        color = colores_clasif.get(clasif, "#ffffff")
        nombre = nombres_clasif.get(clasif, f"Clase {clasif}")
        total = totales_por_clasif[clasif]
        mes_pico, valor_pico = meses_pico[clasif]
        
        st.markdown(f"""
        <p style="color: white; margin: 5px 0;">
            <span style="color: {color};">■</span> <strong>{nombre}</strong>: 
            {int(total):,} casos en total | 
            Pico en {labels[mes_pico-1]} con {int(valor_pico):,} casos
        </p>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Gráfico de pastel para la distribución total
    col1, col2 = st.columns(2)
    
    with col1:
        # Crear figura para pastel
        fig_pie, ax_pie = plt.subplots(figsize=(6, 6), facecolor='#1e1e2f')
        fig_pie.patch.set_facecolor('#1e1e2f')
        
        # Datos para el gráfico
        pie_data = totales_por_clasif.values
        pie_labels = [nombres_clasif.get(c, f"Clase {c}") for c in totales_por_clasif.index]
        pie_colors = [colores_clasif.get(c, "#ffffff") for c in totales_por_clasif.index]
        
        # Crear gráfico de pastel
        wedges, texts, autotexts = ax_pie.pie(
            pie_data,
            labels=pie_labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=pie_colors,
            wedgeprops=dict(width=0.5, edgecolor='white', linewidth=0.5)
        )
        
        # Personalizar textos
        for text, autotext in zip(texts, autotexts):
            text.set_color('white')
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax_pie.axis('equal')
        ax_pie.set_title("Distribución Total por Clasificación", color='white', fontsize=14)
        
        st.pyplot(fig_pie)
    
    with col2:
        # Evolución temporal por clasificación
        st.markdown("### Tendencia temporal por clasificación")
        
        # Crear tabla pivoteada para mostrar evolución
        tabla_evol = pivotado.copy()
        tabla_evol.index = labels
        
        # Renombrar columnas
        tabla_evol.columns = [nombres_clasif.get(c, f"Clase {c}") for c in tabla_evol.columns]
        
        # Mostrar tabla
        st.dataframe(tabla_evol.style.background_gradient(
            cmap='viridis',
            axis=None,
            vmin=0,
            vmax=max(totales_por_clasif)
        ).format("{:,.0f}"))


st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)
# === GRÁFICA 1: EDAD vs INTUBADO ===
# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución de Intubación por Rangos de Edad</h3>
</div>
""", unsafe_allow_html=True)

# Filtrar solo valores válidos y con fecha
df_intubado_edad = df[df['INTUBADO'].isin([1, 2]) & df['EDAD'].notna()].copy()

# Crear rangos de edad
# Crear bins y etiquetas correctamente (10-intervalos)
bins = list(range(0, 101, 10)) + [120]  # [0,10,20,...,100,120] → 12 valores → 11 intervalos
labels_rangos = [f"{i}-{i+9}" for i in range(0, 100, 10)] + ["100+"]  # solo 11 etiquetas

# Aplicar corte sin error
df_intubado_edad['RANGO_EDAD'] = pd.cut(df_intubado_edad['EDAD'], bins=bins, labels=labels_rangos, right=False)
df_intubado_edad['ESTADO_INTUBADO'] = df_intubado_edad['INTUBADO'].map({1: 'Sí', 2: 'No'})

# Agrupar por rango e intubación
conteo_edad = df_intubado_edad.groupby(['RANGO_EDAD', 'ESTADO_INTUBADO']).size().reset_index(name='PACIENTES')

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig1, ax1 = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig1.patch.set_facecolor('#1e1e2f')

# Colores personalizados
color_intubado_si = "#e74c3c"  # Rojo para intubados
color_intubado_no = "#2ecc71"  # Verde para no intubados

# Crear gráfico de barras con colores personalizados y transparencia
bars = sns.barplot(
    data=conteo_edad, 
    x='RANGO_EDAD', 
    y='PACIENTES', 
    hue='ESTADO_INTUBADO', 
    palette={
        "Sí": color_intubado_si, 
        "No": color_intubado_no
    },
    alpha=0.8,
    ax=ax1
)

# Personalización avanzada del gráfico
ax1.set_facecolor('#1e1e2f')
ax1.set_title("Pacientes Intubados por Rango de Edad", fontsize=16, pad=20, color='white')
ax1.set_xlabel("Rango de Edad", fontsize=12, color='white')
ax1.set_ylabel("Número de Pacientes", fontsize=12, color='white')

# Mejorar el diseño del eje X
plt.xticks(rotation=45, ha='right', color='white')
plt.yticks(color='white')
ax1.grid(axis='y', linestyle='--', alpha=0.3, color='gray')

# Mejorar la leyenda
legend = ax1.legend(title="Estado de Intubación", frameon=True, facecolor='#222244', edgecolor='gray')
legend.get_title().set_color('white')
for text in legend.get_texts():
    text.set_color('white')

# Añadir bordes sutiles a las barras para mejor visibilidad
for bar in ax1.patches:
    bar.set_edgecolor('white')
    bar.set_linewidth(0.5)

# Añadir línea de contorno al gráfico
for spine in ax1.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Añadir números en las barras para valores significativos
for bar in ax1.patches:
    height = bar.get_height()
    if height > 0:
        if height > max(conteo_edad["PACIENTES"]) * 0.05:  # Solo mostrar valores significativos
            ax1.text(
                bar.get_x() + bar.get_width() / 2.,
                bar.get_height() + 5,
                f'{int(height):,}',
                ha='center', va='bottom',
                color='white', fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2", fc='#222244', alpha=0.7, ec="gray")
            )

# Ajustar el diseño
plt.tight_layout()

# Mostrar el gráfico
st.pyplot(fig1)

# Añadir análisis adicional
with st.expander("Detalles del análisis por rango de edad"):
    # Calcular estadísticas de intubación por rango
    pivot_edad = conteo_edad.pivot(index='RANGO_EDAD', columns='ESTADO_INTUBADO', values='PACIENTES').fillna(0)
    
    # Asegurar que ambas columnas existan
    if 'Sí' not in pivot_edad.columns:
        pivot_edad['Sí'] = 0
    if 'No' not in pivot_edad.columns:
        pivot_edad['No'] = 0
        
    # Calcular porcentaje de intubados por rango
    pivot_edad['Total'] = pivot_edad['Sí'] + pivot_edad['No']
    pivot_edad['% Intubados'] = (pivot_edad['Sí'] / pivot_edad['Total'] * 100).round(1)
    
    # Encontrar el rango con mayor porcentaje de intubación
    max_porc_rango = pivot_edad['% Intubados'].idxmax()
    max_porc_valor = pivot_edad.loc[max_porc_rango, '% Intubados']
    
    # Encontrar el rango con más pacientes intubados
    max_casos_rango = pivot_edad['Sí'].idxmax()
    max_casos_valor = pivot_edad.loc[max_casos_rango, 'Sí']
    
    # Mostrar estadísticas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-top: 10px;">
            <p style="color: white; margin: 0;">Total de pacientes <span style="color: {color_intubado_si};">Intubados</span>: {int(pivot_edad['Sí'].sum()):,}</p>
            <p style="color: white; margin: 0;">Total de pacientes <span style="color: {color_intubado_no};">No Intubados</span>: {int(pivot_edad['No'].sum()):,}</p>
            <p style="color: white; margin: 0;">Rango de edad con más pacientes intubados: {max_casos_rango} ({int(max_casos_valor):,} pacientes)</p>
            <p style="color: white; margin: 0;">Rango de edad con mayor % de intubación: {max_porc_rango} ({max_porc_valor:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Crear gráfico de línea para mostrar el porcentaje de intubación por rango de edad
        fig_line, ax_line = plt.subplots(figsize=(8, 5), facecolor='#1e1e2f')
        fig_line.patch.set_facecolor('#1e1e2f')
        
        # Gráfico de línea
        ax_line.plot(
            pivot_edad.index, 
            pivot_edad['% Intubados'],
            marker='o',
            markersize=8,
            linewidth=2,
            color="#e74c3c",
            alpha=0.9
        )
        
        # Personalización
        ax_line.set_facecolor('#1e1e2f')
        ax_line.set_title("Porcentaje de Intubación por Rango de Edad", fontsize=14, color='white')
        ax_line.set_xlabel("Rango de Edad", fontsize=10, color='white')
        ax_line.set_ylabel("Porcentaje (%)", fontsize=10, color='white')
        ax_line.set_ylim(bottom=0)
        
        # Etiquetas y grilla
        plt.xticks(rotation=45, ha='right', color='white', fontsize=9)
        plt.yticks(color='white')
        ax_line.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
        
        # Añadir valores en cada punto
        for i, (idx, row) in enumerate(pivot_edad.iterrows()):
            ax_line.text(
                i, row['% Intubados'] + 1,
                f"{row['% Intubados']:.1f}%",
                ha='center',
                va='bottom',
                color='white',
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.2", fc='#222244', alpha=0.7, ec="gray")
            )
        
        # Mostrar gráfico
        st.pyplot(fig_line)
        
    # Tabla de datos
    st.markdown("### Datos detallados por rango de edad")
    
    # Preparar tabla para mostrar
    tabla_edad = pivot_edad.reset_index()
    tabla_edad = tabla_edad[['RANGO_EDAD', 'Sí', 'No', 'Total', '% Intubados']]
    tabla_edad.columns = ['Rango de Edad', 'Intubados', 'No Intubados', 'Total', '% Intubados']
    
    # Formatear valores numéricos
    for col in ['Intubados', 'No Intubados', 'Total']:
        tabla_edad[col] = tabla_edad[col].astype(int).apply(lambda x: f"{x:,}")
    tabla_edad['% Intubados'] = tabla_edad['% Intubados'].apply(lambda x: f"{x:.1f}%")
    
    # Mostrar tabla
    st.table(tabla_edad)

# Añadir separador visual antes del siguiente gráfico
st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)


# === GRÁFICA 2: COMORBILIDAD vs DEFUNCIONES ===
# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución de Comorbilidades en Pacientes Fallecidos</h3>
</div>
""", unsafe_allow_html=True)

# Filtrar defunciones válidas
df_def = df[df['FECHA_DEF'].notna() & (df['FECHA_DEF'] != '9999-99-99')].copy()

# Comorbilidades a considerar
cols_comorb = [
    "DIABETES", "HIPERTENSION", "OBESIDAD", "RENAL_CRONICA",
    "CARDIOVASCULAR", "EPOC", "ASMA", "INMUSUPR", "TABAQUISMO", "OTRA_COM"
]

# Diccionario para nombres más legibles
nombres_legibles = {
    "DIABETES": "Diabetes",
    "HIPERTENSION": "Hipertensión",
    "OBESIDAD": "Obesidad",
    "RENAL_CRONICA": "Enfermedad Renal",
    "CARDIOVASCULAR": "Enfermedad Cardiovascular",
    "EPOC": "EPOC",
    "ASMA": "Asma",
    "INMUSUPR": "Inmunosupresión",
    "TABAQUISMO": "Tabaquismo",
    "OTRA_COM": "Otras comorbilidades"
}

# Contar cuántos fallecidos tienen cada comorbilidad (valor = 1)
conteo_comorb = {
    nombres_legibles.get(col, col): df_def[df_def[col] == 1].shape[0]
    for col in cols_comorb if col in df_def.columns
}

# Quitar comorbilidades con 0 ocurrencias y ordenar por frecuencia descendente
conteo_comorb = dict(sorted({k: v for k, v in conteo_comorb.items() if v > 0}.items(), 
                            key=lambda item: item[1], 
                            reverse=True))

# Total de pacientes fallecidos
total_fallecidos = len(df_def)

# Total de comorbilidades (suma de todas las apariciones)
total_comorbilidades = sum(conteo_comorb.values())

# Calcular porcentajes sobre el total de fallecidos
porcentajes_sobre_fallecidos = {k: (v / total_fallecidos) * 100 for k, v in conteo_comorb.items()}

# Colores atractivos para tema oscuro
colors = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
    "#1abc9c", "#e67e22", "#34495e", "#7f8c8d", "#d35400"
]

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig, ax = plt.subplots(figsize=(10, 8), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Crear gráfico de pastel mejorado
wedges, texts, autotexts = ax.pie(
    conteo_comorb.values(),
    labels=None,  # Quitamos las etiquetas para usar una leyenda separada
    autopct='%1.1f%%',
    startangle=90,
    wedgeprops=dict(width=0.5, edgecolor='white', linewidth=0.5),  # Donut con borde blanco
    pctdistance=0.85,  # Mover los porcentajes más hacia afuera
    colors=colors[:len(conteo_comorb)]
)

# Personalizar textos de porcentajes
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(7)
    autotext.set_weight('bold')

# Añadir un círculo en el centro para un efecto donut más pronunciado
centre_circle = plt.Circle((0, 0), 0.35, fc='#1e1e2f')
ax.add_patch(centre_circle)

# Añadir información dentro del círculo central
ax.annotate(
    f"{total_fallecidos:,}\nFallecidos",
    xy=(0, 0),
    ha='center',
    va='center',
    fontsize=14,
    fontweight='bold',
    color='white'
)

# Ajustar la leyenda para mejor visibilidad
ax.legend(
    wedges,
    [f"{k} ({int(v):,})" for k, v in conteo_comorb.items()],
    title="Comorbilidades",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.5, 1),
    frameon=True,
    facecolor='#222244',
    edgecolor='gray',
    fontsize=10
)

# Personalizar más el gráfico
ax.set_title("Comorbilidades en Pacientes Fallecidos", fontsize=16, pad=20, color='white')
ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

# Pie de gráfico con información
fig.text(
    0.5, 0.02,
    f"* Los porcentajes representan la proporción de cada comorbilidad sobre el total de {total_comorbilidades:,} comorbilidades registradas",
    ha='center',
    color='white',
    fontsize=9,
    alpha=0.7
)

# Mostrar gráfico
st.pyplot(fig)

# Añadir análisis expandible
with st.expander("Análisis detallado de comorbilidades en fallecidos"):
    # Tabla comparativa
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Crear tabla de datos
        tabla_data = []
        for nombre, conteo in conteo_comorb.items():
            porc_sobre_fallecidos = porcentajes_sobre_fallecidos[nombre]
            porc_sobre_comorb = (conteo / total_comorbilidades) * 100
            tabla_data.append({
                "Comorbilidad": nombre,
                "Casos": f"{conteo:,}",
                "% de fallecidos": f"{porc_sobre_fallecidos:.1f}%",
                "% de comorbilidades": f"{porc_sobre_comorb:.1f}%"
            })
        
        tabla_df = pd.DataFrame(tabla_data)
        st.table(tabla_df)
    
    with col2:
        # Estadísticas clave
        # Promedio de comorbilidades por fallecido
        n_fallecidos_con_comorb = df_def[df_def[cols_comorb].eq(1).any(axis=1)].shape[0]
        promedio_comorb = total_comorbilidades / n_fallecidos_con_comorb if n_fallecidos_con_comorb > 0 else 0
        
        st.markdown("""
        <div style="background-color: #222244; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
            <h4 style="color: white; margin-top: 0;">Estadísticas clave</h4>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <p style="color: white; margin: 5px 0;">Total de fallecidos: <strong>{total_fallecidos:,}</strong></p>
            <p style="color: white; margin: 5px 0;">Fallecidos con al menos una comorbilidad: <strong>{n_fallecidos_con_comorb:,}</strong> ({n_fallecidos_con_comorb/total_fallecidos*100:.1f}%)</p>
            <p style="color: white; margin: 5px 0;">Promedio de comorbilidades por fallecido: <strong>{promedio_comorb:.2f}</strong></p>
            <p style="color: white; margin: 5px 0;">Comorbilidad más frecuente: <strong>{list(conteo_comorb.keys())[0]}</strong> ({list(conteo_comorb.values())[0]:,} casos)</p>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Comparación con población general
        if df_confirmados is not None and len(df_confirmados) > 0:
            # Calcular las diferencias en porcentajes de comorbilidades entre fallecidos y confirmados en general
            diferencias_porc = {}
            for col in cols_comorb:
                if col in df_confirmados.columns:
                    porc_general = (df_confirmados[df_confirmados[col] == 1].shape[0] / len(df_confirmados)) * 100
                    porc_fallecidos = (df_def[df_def[col] == 1].shape[0] / total_fallecidos) * 100 if total_fallecidos > 0 else 0
                    nombre = nombres_legibles.get(col, col)
                    diferencias_porc[nombre] = porc_fallecidos - porc_general
            
            # Ordenar diferencias por valor descendente
            diferencias_porc = dict(sorted(diferencias_porc.items(), key=lambda item: item[1], reverse=True))
            
            # Mostrar las diferencias más significativas (>5%)
            st.markdown("""
            <div style="background-color: #222244; padding: 15px; border-radius: 5px;">
                <h4 style="color: white; margin-top: 0;">Comorbilidades más frecuentes en fallecidos vs. población general</h4>
            """, unsafe_allow_html=True)
            
            for nombre, diferencia in diferencias_porc.items():
                if abs(diferencia) > 5:  # Solo mostrar diferencias significativas
                    color = "#e74c3c" if diferencia > 0 else "#2ecc71"
                    st.markdown(f"""
                    <p style="color: white; margin: 5px 0;">
                        <strong>{nombre}</strong>: <span style="color: {color};">{'+' if diferencia > 0 else ''}{diferencia:.1f}%</span> 
                        más {'frecuente' if diferencia > 0 else 'rara'} en fallecidos
                    </p>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>", unsafe_allow_html=True)
#-----------------------------------------------------
#-----------------------------------------------------
# === Gráfico: Días entre inicio de síntomas e ingreso (0–20 días, en pasos de 2) ===
# Crear un contenedor con estilo
st.markdown("""
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Días desde Inicio de Síntomas hasta Ingreso Hospitalario</h3>
</div>
""", unsafe_allow_html=True)

# Asegurar fechas válidas
df_fechas = df.copy()
df_fechas['FECHA_SINTOMAS'] = pd.to_datetime(df_fechas['FECHA_SINTOMAS'], errors='coerce')
df_fechas['FECHA_INGRESO'] = pd.to_datetime(df_fechas['FECHA_INGRESO'], errors='coerce')

# Calcular diferencia de días
df_fechas = df_fechas[df_fechas['FECHA_SINTOMAS'].notna() & df_fechas['FECHA_INGRESO'].notna()]
df_fechas['DIFERENCIA_DIAS'] = (df_fechas['FECHA_INGRESO'] - df_fechas['FECHA_SINTOMAS']).dt.days

# Filtrar días entre 0 y 20
df_dias = df_fechas[(df_fechas['DIFERENCIA_DIAS'] >= 0) & (df_fechas['DIFERENCIA_DIAS'] <= 20)]

# Bins de 2 en 2
bins = list(range(0, 22, 2))  # 0–2, 2–4, ..., 20
labels = [f"{i}-{i+1}" for i in range(0, 20, 2)]

# Configurar tema oscuro para Matplotlib
plt.style.use('dark_background')

# Crear figura con tamaño mejorado y fondo oscuro
fig, ax = plt.subplots(figsize=(14, 7), facecolor='#1e1e2f')
fig.patch.set_facecolor('#1e1e2f')

# Crear histograma con un solo color base (arreglando el error)
# Usamos un solo color para el histograma en lugar de un array de colores
color_base = "#3498db"  # Azul para el histograma
counts, edges, bars = ax.hist(
    df_dias['DIFERENCIA_DIAS'], 
    bins=bins, 
    edgecolor='white',
    linewidth=0.8,
    color=color_base,
    alpha=0.8
)

# Personalizar el gráfico
ax.set_facecolor('#1e1e2f')
ax.set_title("Distribución de Días con Síntomas antes del Ingreso Hospitalario", fontsize=16, pad=20, color='white')
ax.set_xlabel("Días desde inicio de síntomas hasta ingreso", fontsize=12, color='white', labelpad=10)
ax.set_ylabel("Número de Pacientes", fontsize=12, color='white', labelpad=10)

# Eje Y sin notación científica
import matplotlib.ticker as ticker
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{int(x):,}'))

# Eje X con ticks pares y etiquetas mejoradas
ax.set_xticks(list(range(0, 21, 2)))  # 0, 2, 4, ..., 20
ax.tick_params(axis='both', colors='white', labelsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.3, color='gray')

# Mostrar valores encima de las barras
for i, (count, bar) in enumerate(zip(counts, bars)):
    height = bar.get_height()
    if height > 0:
        ax.annotate(
            f'{int(count):,}', 
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5), 
            textcoords="offset points",
            ha='center', 
            va='bottom', 
            fontsize=9,
            color='white',
            bbox=dict(boxstyle="round,pad=0.2", fc='#222244', alpha=0.7, ec="gray")
        )

# Añadir línea de contorno al gráfico
for spine in ax.spines.values():
    spine.set_edgecolor('gray')
    spine.set_linewidth(0.5)

# Ajustar el diseño
plt.tight_layout()

# Mostrar gráfico
st.pyplot(fig)

# #--------------------------------
# st.markdown("## Influencia de Comorbilidades en la Intubación")

# Filtrar pacientes con INTUBADO válido

# # Filtrar pacientes con INTUBADO válido
# df_intub = df[df['INTUBADO'].isin([1, 2])].copy()

# # Comorbilidades a evaluar
# comorbilidades = [
#     "DIABETES", "HIPERTENSION", "OBESIDAD", "RENAL_CRONICA",
#     "CARDIOVASCULAR", "EPOC", "ASMA", "INMUSUPR", "TABAQUISMO", "OTRA_COM"
# ]

# # Construcción de tabla
# data = []
# for col in comorbilidades:
#     if col in df_intub.columns:
#         total = df_intub[df_intub[col] == 1]
#         n_total = len(total)
#         n_intub = len(total[total['INTUBADO'] == 1])
#         pct = round((n_intub / n_total) * 100, 1) if n_total > 0 else 0
#         data.append({
#             "Comorbilidad": col,
#             "Total con comorbilidad": n_total,
#             "Intubados": n_intub,
#             "% Intubados": pct
#         })

# # Crear DataFrame y ordenar por % Intubados DESC
# df_result = pd.DataFrame(data).sort_values(by="% Intubados", ascending=False)

# # Asegurarse de que el índice esté completamente limpio
# df_result = df_result.reset_index(drop=True)

# # Estilo corregido para fondo claro y texto visible
# styled_table = df_result.style\
#     .format({
#         "Total con comorbilidad": "{:,}",
#         "Intubados": "{:,}",
#         "% Intubados": "{:.1f} %"
#     })\
#     .set_properties({
#         'text-align': 'center',
#         'font-family': 'Arial',
#         'font-size': '14px',
#         'color': 'black',
#         'background-color': '#f0f0f0',
#         'border': '1px solid #ddd'  # Añadir borde a las celdas
#     })\
#     .set_table_styles([{
#         'selector': 'th',
#         'props': [
#             ('font-weight', 'bold'),
#             ('background-color', '#444'),
#             ('color', 'white'),
#             ('padding', '8px'),
#             ('border', '1px solid #ddd')
#         ]
#     }, {
#         'selector': 'td',
#         'props': [
#             ('padding', '8px'),
#             ('border', '1px solid #ddd')
#         ]
#     }])\
#     .hide(axis="index")

# # Mostrar tabla con diseño mejorado
# st.markdown(styled_table.to_html(), unsafe_allow_html=True)