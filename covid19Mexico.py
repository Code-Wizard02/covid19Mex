import streamlit as st
import pandas as pd
import pymysql
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import matplotlib.ticker as ticker

def divisor_visual():
    st.markdown(
        "<hr style='margin: 30px 0; border: 0; border-top: 2px solid #bbb;'>",
        unsafe_allow_html=True,
    )

def encabezado_grafica(titulo):
    st.markdown(
        f"""
        <div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
            <h3 style="color: #ffffff; margin-top: 0; text-align: center;">{titulo}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    ) 

# --- Conexión a MySQL ---
def get_mysql_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Wizardkiller#02",
        database="covid19",
        cursorclass=pymysql.cursors.Cursor,
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
    "2023": "covid19_2023",
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

    regiones = df["REGION"].dropna().unique()
    region_seleccionada = st.sidebar.selectbox(
        "Selecciona una Región", sorted(regiones)
    )

    entidades = df[df["REGION"] == region_seleccionada]["ENTIDAD"].dropna().unique()
    entidad_seleccionada = st.sidebar.selectbox(
        "Selecciona una Entidad Federativa", sorted(entidades)
    )

    df_filtrado = df[
        (df["REGION"] == region_seleccionada) & (df["ENTIDAD"] == entidad_seleccionada)
    ]

    if st.sidebar.button("Actualizar datos"):
        if "cache_dfs" in st.session_state:
            del st.session_state.cache_dfs[seleccion]
    st.cache_data.clear()

else:
    st.warning("La tabla está vacía o ocurrió un error al cargar los datos.")

# KPIs
encabezado_grafica("Indicadores Clave de Desempeño (KPIs)")

# Filtrados para los KPIs
df_confirmados = df_filtrado[df_filtrado["CLASIFICACION_FINAL"] == 1]
total_confirmados = len(df_confirmados)
total_negativos = len(df_filtrado[df_filtrado["CLASIFICACION_FINAL"] == 2])
total_sospechosos = len(df_filtrado[df_filtrado["CLASIFICACION_FINAL"] == 3])

defunciones = df_confirmados[
    df_confirmados["FECHA_DEF"].notna() & (df_confirmados["FECHA_DEF"] != "9999-99-99")
]
total_defunciones = len(defunciones)


df_confirmados["FECHA_DEF"] = df_confirmados["FECHA_DEF"].astype(str)
total_recuperados = len(df_confirmados[df_confirmados["FECHA_DEF"] == "9999-99-99"])


hombres = len(df_confirmados[df_confirmados["SEXO"] == 1])
mujeres = len(df_confirmados[df_confirmados["SEXO"] == 2])
porc_hombres = (
    round((hombres / total_confirmados) * 100, 1) if total_confirmados > 0 else 0
)
porc_mujeres = (
    round((mujeres / total_confirmados) * 100, 1) if total_confirmados > 0 else 0
)

hospitalizados = len(df_confirmados[df_confirmados["TIPO_PACIENTE"] == 2])
ambulatorios = len(df_confirmados[df_confirmados["TIPO_PACIENTE"] == 1])
porc_hosp = (
    round((hospitalizados / total_confirmados) * 100, 1) if total_confirmados > 0 else 0
)
porc_ambu = (
    round((ambulatorios / total_confirmados) * 100, 1) if total_confirmados > 0 else 0
)


def porcentaje_condicion(col):
    if col in df_confirmados.columns:
        return round(
            (len(df_confirmados[df_confirmados[col] == 1]) / total_confirmados) * 100, 1
        )
    return 0

comorbilidades = {
    "Diabetes": porcentaje_condicion("DIABETES"),
    "Hipertensión": porcentaje_condicion("HIPERTENSION"),
    "Obesidad": porcentaje_condicion("OBESIDAD"),
    "Renal Crónica": porcentaje_condicion("RENAL_CRONICA"),
    "Cardiovascular": porcentaje_condicion("CARDIOVASCULAR"),
    "Tabaquismo": porcentaje_condicion("TABAQUISMO"),
}

# Dividir los KPIs en columnas
color_confirmados = "#e74c3c"  # Rojo
color_negativos = "#3498db"  # Azul
color_sospechosos = "#f39c12"  # Naranja
color_defunciones = "#7f8c8d"  # Gris
color_recuperados = "#e67e22"  # Naranja oscuro
color_activos = "#2ecc71"  # Verde

# Formateo de números
def format_number(num):
    return f"{num:,}".replace(",", ",")


st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_confirmados};"></div>
            <div class="kpi-icon"><i class="fas fa-virus"></i></div>
            <div class="kpi-title">CONFIRMADOS</div>
            <div class="kpi-value">{format_number(total_confirmados)}</div>
            <div class="kpi-subtitle">Casos acumulados</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_negativos};"></div>
            <div class="kpi-icon"><i class="fas fa-shield-virus"></i></div>
            <div class="kpi-title">NEGATIVOS</div>
            <div class="kpi-value">{format_number(total_negativos)}</div>
            <div class="kpi-subtitle">Casos acumulados</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_sospechosos};"></div>
            <div class="kpi-icon"><i class="fas fa-question-circle"></i></div>
            <div class="kpi-title">SOSPECHOSOS</div>
            <div class="kpi-value">{format_number(total_sospechosos)}</div>
            <div class="kpi-subtitle">Casos acumulados</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

col4, col5, col6 = st.columns(3)
with col4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_defunciones};"></div>
            <div class="kpi-icon"><i class="fas fa-procedures"></i></div>
            <div class="kpi-title">DEFUNCIONES</div>
            <div class="kpi-value">{format_number(total_defunciones)}</div>
            <div class="kpi-subtitle">Acumulados</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with col5:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_recuperados};"></div>
            <div class="kpi-icon"><i class="fas fa-heartbeat"></i></div>
            <div class="kpi-title">RECUPERADOS</div>
            <div class="kpi-value">{format_number(total_recuperados)}</div>
            <div class="kpi-subtitle">Acumulados</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with col6:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_activos};"></div>
            <div class="kpi-icon"><i class="fas fa-user-friends"></i></div>
            <div class="kpi-title">HOMBRES / MUJERES</div>
            <div class="kpi-value">{porc_hombres}% / {porc_mujeres}%</div>
            <div class="kpi-subtitle">Distribución por género</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

col7, col8 = st.columns(2)
with col7:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_defunciones};"></div>
            <div class="kpi-icon"><i class="fas fa-hospital"></i></div>
            <div class="kpi-title">HOSPITALIZADOS</div>
            <div class="kpi-value">{porc_hosp}%</div>
            <div class="kpi-subtitle">Del total de confirmados</div>
        </div>
    """,
        unsafe_allow_html=True,
    )
with col8:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-left-border" style="background-color: {color_activos};"></div>
            <div class="kpi-icon"><i class="fas fa-home"></i></div>
            <div class="kpi-title">AMBULATORIOS</div>
            <div class="kpi-value">{porc_ambu}%</div>
            <div class="kpi-subtitle">Del total de confirmados</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

divisor_visual();

# Porcentaje de comorbilidades
encabezado_grafica("Comorbilidades Principales")

cols = st.columns(len(comorbilidades))
sorted_comorbilidades = dict(
    sorted(comorbilidades.items(), key=lambda item: item[1], reverse=True)
)

for i, (nombre, valor) in enumerate(sorted_comorbilidades.items()):
    with cols[i]:
        st.markdown(f"**{nombre.upper()}**")
        if valor > 10:
            color = "#d73027"  # Rojo para valores altos
        elif valor > 7:
            color = "#fc8d59"  # Naranja para valores medios
        else:
            color = "#91bfdb"  # Azul para valores bajos

        st.markdown(f"{valor:.2f} %")
        st.markdown(
            f"""
            <div style="background-color: #f0f0f0; border-radius: 3px; height: 10px; width: 100%;">
                <div style="background-color: {color}; width: {min(valor*2, 100)}%; height: 100%; border-radius: 3px;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

suma_total = sum(sorted_comorbilidades.values())


st.markdown(
    "<hr style='margin: 15px 0 10px 0; border: 0; border-top: 1px solid #ccc;'>",
    unsafe_allow_html=True,
)


st.markdown("<div style='padding: 8px 0;'>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 3])
with col1:
    st.markdown(f"**TOTAL DE LA POBLACIÓN**")
    st.markdown(f"{suma_total:.2f} %")
with col2:
    st.markdown(
        f"""
        <div style="background-color: #f0f0f0; border-radius: 3px; height: 12px; width: 100%; margin-top: 22px;">
            <div style="background: linear-gradient(90deg, #d73027, #fc8d59, #91bfdb); 
                        width: {min(suma_total, 100)}%; 
                        height: 100%; 
                        border-radius: 3px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

divisor_visual()

# Gráfico Edad-Sexo
col1, col2 = st.columns(2)
with col1:
    st.markdown(
        """
        <div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
            <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución Demográfica por Edad y Sexo</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

    tipo_caso = st.selectbox(
        "Tipo de caso:",
        ["Confirmados", "Negativos", "Sospechosos"],
        key="grafico_tipo_caso",
    )

    tipo_map = {"Confirmados": 1, "Negativos": 2, "Sospechosos": 3}
    tipo_color = {
        "Confirmados": "#e74c3c",
        "Negativos": "#3498db",
        "Sospechosos": "#f39c12",
    }
    tipo_valor = tipo_map[tipo_caso]

    df_tipo = df[df["CLASIFICACION_FINAL"] == tipo_valor].copy()

    bins = list(range(0, 100, 5)) + [100]
    labels = [f"{i}-{i+4}" for i in range(0, 95, 5)] + ["95+"]
    df_tipo["RANGO_EDAD"] = pd.cut(df_tipo["EDAD"], bins=bins, labels=labels, right=False)
    df_tipo["SEXO"] = df_tipo["SEXO"].map({1: "Hombres", 2: "Mujeres"})

    # Agrupar por rango de edad y sexo
    conteo = df_tipo.groupby(["RANGO_EDAD", "SEXO"]).size().reset_index(name="CASOS")

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
    fig.patch.set_facecolor("#1e1e2f")
    color_hombres = "#3498db"  # Azul para hombres
    color_mujeres = "#e74c3c"  # Rojo para mujeres
    bars = sns.barplot(
        data=conteo,
        x="RANGO_EDAD",
        y="CASOS",
        hue="SEXO",
        palette={"Hombres": color_hombres, "Mujeres": color_mujeres},
        alpha=0.8,
        ax=ax,
    )
    ax.set_facecolor("#1e1e2f")
    ax.set_title(
        f"Distribución por Edad y Sexo - {tipo_caso}", fontsize=16, pad=20, color="white"
    )
    ax.set_xlabel("Rango de Edad", fontsize=12, color="white")
    ax.set_ylabel("Número de Casos", fontsize=12, color="white")
    plt.xticks(rotation=45, ha="right", color="white")
    plt.yticks(color="white")
    ax.grid(axis="y", linestyle="--", alpha=0.3, color="gray")
    legend = ax.legend(title="Género", frameon=True, facecolor="#222244", edgecolor="gray")
    legend.get_title().set_color("white")
    for text in legend.get_texts():
        text.set_color("white")
    for bar in ax.patches:
        bar.set_edgecolor("white")
        bar.set_linewidth(0.5)
    for spine in ax.spines.values():
        spine.set_edgecolor("gray")
        spine.set_linewidth(0.5)
    for bar in ax.patches:
        height = bar.get_height()
        if height > 0:
            if height > max(conteo["CASOS"]) * 0.05:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 5,
                    f"{int(height):,}",
                    ha="center",
                    va="bottom",
                    color="white",
                    fontsize=8,
                )
    plt.tight_layout()
    st.pyplot(fig)

with col2:
# Gráfico Edad - Tipo de Paciente
    st.markdown(
        """
    <div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
        <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución por Edad y Tipo de Atención</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    tipo_caso_tp = st.selectbox(
        "Tipo de caso:",
            ["Confirmados", "Negativos", "Sospechosos"],
            key="grafico_tipo_paciente",
    )

    tipo_valor_tp = tipo_map[tipo_caso_tp]
    df_tipo_tp = df[df["CLASIFICACION_FINAL"] == tipo_valor_tp].copy()

    df_tipo_tp["TIPO_PACIENTE"] = df_tipo_tp["TIPO_PACIENTE"].map(
        {1: "Ambulatorios", 2: "Hospitalizados"}
    )
    df_tipo_tp["RANGO_EDAD"] = pd.cut(
        df_tipo_tp["EDAD"], bins=list(range(0, 100, 5)) + [100], labels=labels, right=False
    )

    conteo_tp = (
        df_tipo_tp.groupby(["RANGO_EDAD", "TIPO_PACIENTE"]).size().reset_index(name="CASOS")
    )
    plt.style.use("dark_background")
    fig2, ax2 = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
    fig2.patch.set_facecolor("#1e1e2f")
    color_ambulatorio = "#2ecc71"  # Verde para ambulatorios
    color_hospitalizado = "#e67e22"  # Naranja para hospitalizados
    bars = sns.barplot(
        data=conteo_tp,
        x="RANGO_EDAD",
        y="CASOS",
        hue="TIPO_PACIENTE",
        palette={"Ambulatorios": color_ambulatorio, "Hospitalizados": color_hospitalizado},
        alpha=0.8,
        ax=ax2,
    )
    ax2.set_facecolor("#1e1e2f")
    ax2.set_title(
        f"Distribución por Edad y Tipo de Atención - {tipo_caso_tp}",
        fontsize=16,
        pad=20,
        color="white",
    )
    ax2.set_xlabel("Rango de Edad", fontsize=12, color="white")
    ax2.set_ylabel("Número de Casos", fontsize=12, color="white")
    plt.xticks(rotation=45, ha="right", color="white")
    plt.yticks(color="white")
    ax2.grid(axis="y", linestyle="--", alpha=0.3, color="gray")
    legend = ax2.legend(
        title="Tipo de Atención", frameon=True, facecolor="#222244", edgecolor="gray"
    )
    legend.get_title().set_color("white")
    for text in legend.get_texts():
        text.set_color("white")
    for bar in ax2.patches:
        bar.set_edgecolor("white")
        bar.set_linewidth(0.5)
    for spine in ax2.spines.values():
        spine.set_edgecolor("gray")
        spine.set_linewidth(0.5)
    for bar in ax2.patches:
        height = bar.get_height()
        if height > 0:
            if (
                height > max(conteo_tp["CASOS"]) * 0.05
            ):
                ax2.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 5,
                    f"{int(height):,}",
                    ha="center",
                    va="bottom",
                    color="white",
                    fontsize=8,
                )

    plt.tight_layout()
    st.pyplot(fig2)
    
divisor_visual();
   # --- Gráfica de pastel: Porcentaje de enfermedades en casos confirmados ---
st.markdown(
    """
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Comorbilidades en Casos Confirmados</h3>
</div>
""",
    unsafe_allow_html=True,
)

# Lista de columnas de enfermedades
columnas_enfermedades = [
    "DIABETES",
    "HIPERTENSION",
    "OBESIDAD",
    "RENAL_CRONICA",
    "CARDIOVASCULAR",
    "EPOC",
    "ASMA",
    "INMUSUPR",
    "TABAQUISMO",
    "OTRA_COM",
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
    "OTRA_COM": "Otras comorbilidades",
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
porcentajes = {
    k: round((v / suma_total) * 100, 1) for k, v in conteo_comorbilidades.items()
}

# Ordenar por porcentaje descendente
porcentajes = dict(sorted(porcentajes.items(), key=lambda item: item[1], reverse=True))

colors = [
    "#3498db",
    "#e74c3c",
    "#2ecc71",
    "#f39c12",
    "#9b59b6",
    "#1abc9c",
    "#e67e22",
    "#34495e",
    "#7f8c8d",
    "#d35400",
]

plt.style.use("dark_background")
fig_pie, ax_pie = plt.subplots(figsize=(10, 8), facecolor="#1e1e2f")
fig_pie.patch.set_facecolor("#1e1e2f")
wedges, texts, autotexts = ax_pie.pie(
    porcentajes.values(),
    labels=None,
    autopct="%1.1f%%",
    startangle=90,
    wedgeprops=dict(
        width=0.5, edgecolor="white", linewidth=0.5
    ),
    pctdistance=0.95,
    colors=colors[: len(porcentajes)],
)

for autotext in autotexts:
    autotext.set_color("white")
    autotext.set_fontsize(7)
    autotext.set_weight("bold")

centre_circle = plt.Circle((0, 0), 0.35, fc="#1e1e2f")
ax_pie.add_patch(centre_circle)
ax_pie.annotate(
    "Comorbilidades",
    xy=(0, 0),
    ha="center",
    va="center",
    fontsize=14,
    fontweight="bold",
    color="white",
)

ax_pie.legend(
    wedges,
    [f"{k} ({v}%)" for k, v in porcentajes.items()],
    title="Comorbilidades",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.5, 1),
    frameon=True,
    facecolor="#222244",
    edgecolor="gray",
    fontsize=10,
)

ax_pie.set_title(
    "Distribución de Comorbilidades en Casos Confirmados",
    fontsize=16,
    pad=20,
    color="white",
)
ax_pie.axis("equal")

# Información adicional
total_casos = len(df_confirmados)
casos_con_comorbilidad = sum(conteo_comorbilidades.values())
porc_con_comorbilidad = round((casos_con_comorbilidad / total_casos) * 100, 1)

fig_pie.text(
    0.5,
    0.02,
    f"Total de casos analizados: {total_casos:,} | Casos con al menos una comorbilidad: {porc_con_comorbilidad}%",
    ha="center",
    color="white",
    fontsize=10,
    alpha=0.7,
)

st.pyplot(fig_pie)
# =================== DIVISOR VISUAL ===================
divisor_visual();

col1, col2 = st.columns(2)
with col1:
# === Gráfico de Línea - Intubados por mes (empezando en 0 en enero y febrero) ===
    st.markdown(
        """
    <div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
        <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Evolución Mensual de Pacientes Intubados</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    df["FECHA_INGRESO"] = pd.to_datetime(df["FECHA_INGRESO"], errors="coerce")
    df_intubado = df[df["FECHA_INGRESO"].notna() & df["INTUBADO"].isin([1, 2])].copy()

    df_intubado["MES"] = df_intubado["FECHA_INGRESO"].dt.month
    conteo_real = (
        df_intubado[df_intubado["MES"] >= 3]
        .groupby(["MES", "INTUBADO"])
        .size()
        .reset_index(name="PACIENTES")
    )
    meses_cero = pd.DataFrame(
        [
            {"MES": mes, "INTUBADO": estado, "PACIENTES": 0}
            for mes in [1, 2]
            for estado in [1, 2]
        ]
    )

    # Unir conteos
    conteo_completo = pd.concat([meses_cero, conteo_real], ignore_index=True)

    # Pivotear
    pivot_intubado = conteo_completo.pivot(
        index="MES", columns="INTUBADO", values="PACIENTES"
    ).fillna(0)

    # Asegurar que todos los meses del 1 al 12 estén presentes
    for mes in range(1, 13):
        if mes not in pivot_intubado.index:
            pivot_intubado.loc[mes] = [0, 0]
    pivot_intubado = pivot_intubado.sort_index()

    etiquetas = {1: "Sí", 2: "No"}
    labels = [
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
    fig.patch.set_facecolor("#1e1e2f")
    color_intubado_si = "#e74c3c"  # Rojo para intubados
    color_intubado_no = "#2ecc71"  # Verde para no intubados
    colores = {1: color_intubado_si, 2: color_intubado_no}
    for col in pivot_intubado.columns:
        ax.plot(
            pivot_intubado.index,
            pivot_intubado[col],
            marker="o",
            markersize=8,
            linewidth=3,
            color=colores.get(col, "#ffffff"),
            label=f"Intubado: {etiquetas.get(col, col)}",
            alpha=0.9,
        )
    ax.set_facecolor("#1e1e2f")
    ax.set_title(
        "Evolución Mensual de Pacientes Intubados", fontsize=18, pad=20, color="white"
    )
    ax.set_xlabel("Mes", fontsize=14, color="white", labelpad=10)
    ax.set_ylabel("Número de Pacientes", fontsize=14, color="white", labelpad=10)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(labels, color="white", fontsize=12)
    ax.tick_params(axis="y", colors="white", labelsize=12)
    ax.grid(axis="both", linestyle="--", alpha=0.3, color="gray")

    legend = ax.legend(
        title="Estado de Intubación",
        frameon=True,
        facecolor="#222244",
        edgecolor="gray",
        fontsize=12,
        loc="upper left",
    )
    legend.get_title().set_color("white")
    legend.get_title().set_fontsize(13)
    for text in legend.get_texts():
        text.set_color("white")

    for col in pivot_intubado.columns:
        for mes, valor in enumerate(pivot_intubado[col], 1):
            if valor > 0:
                ax.annotate(
                    f"{int(valor):,}",
                    xy=(mes, valor),
                    xytext=(
                        0,
                        10 if col == 1 else -20,
                    ),
                    textcoords="offset points",
                    ha="center",
                    va="bottom" if col == 1 else "top",
                    color="white",
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="#222244", alpha=0.7, ec="gray"),
                )

    for spine in ax.spines.values():
        spine.set_edgecolor("gray")
        spine.set_linewidth(0.5)

    plt.tight_layout()

    st.pyplot(fig)


with col2:
# --- Distribución por Edad en Rangos (Histograma) ---
    st.markdown(
        """
    <div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
        <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución de Casos Sospechosos por Mes</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Convertir fecha y filtrar clasificaciones válidas
    df_sospechosos = df.copy()
    df_sospechosos["FECHA_INGRESO"] = pd.to_datetime(
        df_sospechosos["FECHA_INGRESO"], errors="coerce"
    )
    df_sospechosos = df_sospechosos[df_sospechosos["CLASIFICACION_FINAL"].isin([3, 6, 7])]
    df_sospechosos = df_sospechosos[df_sospechosos["FECHA_INGRESO"].notna()].copy()

    # Extraer mes
    df_sospechosos["MES"] = df_sospechosos["FECHA_INGRESO"].dt.month

    # Conteo real desde abril en adelante
    conteo_real = (
        df_sospechosos[df_sospechosos["MES"] >= 4]
        .groupby(["MES", "CLASIFICACION_FINAL"])
        .size()
        .reset_index(name="PACIENTES")
    )

    # Agregar ceros para enero-marzo
    meses_cero = pd.DataFrame(
        [
            {"MES": mes, "CLASIFICACION_FINAL": clasif, "PACIENTES": 0}
            for mes in [1, 2, 3]
            for clasif in [3, 6, 7]
        ]
    )

    # Combinar conteos
    conteo_completo = pd.concat([meses_cero, conteo_real], ignore_index=True)
    pivotado = conteo_completo.pivot(
        index="MES", columns="CLASIFICACION_FINAL", values="PACIENTES"
    ).fillna(0)

    # Asegurar que todos los meses del 1 al 12 estén presentes
    for mes in range(1, 13):
        if mes not in pivotado.index:
            pivotado.loc[mes] = [0, 0, 0]
    pivotado = pivotado.sort_index()

    # Etiquetas y colores mejorados
    labels = [
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]
    colores_clasif = {3: "#f39c12", 6: "#3498db", 7: "#2ecc71"}  # Naranja  # Azul  # Verde
    nombres_clasif = {3: "Sospechoso", 6: "Probable", 7: "Negativo"}

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
    fig.patch.set_facecolor("#1e1e2f")

    x = np.arange(len(labels))
    width = 0.25
    offset = 0
    for i, clasif in enumerate(pivotado.columns):
        bars = ax.bar(
            x + offset,
            pivotado[clasif],
            width,
            label=nombres_clasif.get(clasif, f"Clase {clasif}"),
            color=colores_clasif.get(clasif, "#ffffff"),
            edgecolor="white",
            linewidth=0.5,
            alpha=0.8,
        )

        umbral = (
            max(pivotado[clasif]) * 0.1
        )  # Solo mostrar valores para barras con > 10% del máximo
        for j, bar in enumerate(bars):
            height = bar.get_height()
            if height > umbral:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + 5,
                    f"{int(height):,}",
                    ha="center",
                    va="bottom",
                    color="white",
                    fontsize=8,
                    rotation=0,
                    bbox=dict(boxstyle="round,pad=0.2", fc="#222244", alpha=0.7, ec="gray"),
                )
        offset += width

    ax.set_facecolor("#1e1e2f")
    ax.set_title(
        "Evolución Mensual de Casos por Tipo de Clasificación",
        fontsize=16,
        pad=20,
        color="white",
    )
    ax.set_xlabel("Mes", fontsize=12, color="white")
    ax.set_ylabel("Número de Pacientes", fontsize=12, color="white")
    ax.set_xticks(x + width)
    ax.set_xticklabels(labels, color="white")
    ax.tick_params(axis="y", colors="white")
    ax.grid(axis="y", linestyle="--", alpha=0.3, color="gray")
    legend = ax.legend(
        title="Clasificación Final",
        frameon=True,
        facecolor="#222244",
        edgecolor="gray",
        fontsize=10,
        loc="upper left",
    )
    legend.get_title().set_color("white")
    for text in legend.get_texts():
        text.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("gray")
        spine.set_linewidth(0.5)

    plt.tight_layout()
    st.pyplot(fig)
    
# =================== DIVISOR VISUAL ===================
divisor_visual();

# --- Gráfico de barras horizontales: comorbilidades en confirmados o fallecidos ---
encabezado_grafica("Comorbilidades en Casos Confirmados o Fallecidos")

# Selector de tipo de analisis
tipo_comparacion = st.radio(
    "Selecciona el grupo a analizar:",
    ("Casos Confirmados", "Casos Fallecidos"),
    horizontal=True,
    key="comorbilidades_tipo",
)

# Filtrar DataFrame según la selección
if tipo_comparacion == "Casos Confirmados":
    df_comorbilidad = df[df["CLASIFICACION_FINAL"] == 1].copy()
    color_base = "#3498db"  # Azul para confirmados
else:
    df_comorbilidad = df[
        (df["CLASIFICACION_FINAL"] == 1)
        & (df["FECHA_DEF"].notna())
        & (df["FECHA_DEF"] != "9999-99-99")
    ].copy()
    color_base = "#e74c3c"  # Rojo para fallecidos

# Columnas de comorbilidades
columnas_comorb = [
    "DIABETES",
    "HIPERTENSION",
    "OBESIDAD",
    "EPOC",
    "ASMA",
    "CARDIOVASCULAR",
    "RENAL_CRONICA",
    "TABAQUISMO",
    "INMUSUPR",
    "OTRA_COM",
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
    "OTRA_COM": "Otras comorbilidades",
}

# Calcular frecuencias (solo donde el valor es 1)
frecuencias = {
    nombres_legibles.get(col, col): df_comorbilidad[df_comorbilidad[col] == 1].shape[0]
    for col in columnas_comorb
    if col in df_comorbilidad.columns
}

# Calcular porcentajes sobre el total de pacientes
total_pacientes = len(df_comorbilidad)
porcentajes = {k: (v / total_pacientes) * 100 for k, v in frecuencias.items()}

# Convertir a DataFrame y ordenar
df_comorb_plot = pd.DataFrame({"Pacientes": frecuencias, "Porcentaje": porcentajes})
df_comorb_plot = df_comorb_plot.sort_values(by="Pacientes", ascending=True)

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(12, 8), facecolor="#1e1e2f")
fig.patch.set_facecolor("#1e1e2f")
cmap = plt.cm.get_cmap("YlOrRd" if tipo_comparacion == "Casos Fallecidos" else "YlGnBu")
colors = cmap(np.linspace(0.3, 1.0, len(df_comorb_plot)))
bars = ax.barh(
    df_comorb_plot.index,
    df_comorb_plot["Pacientes"],
    color=colors,
    edgecolor="white",
    linewidth=0.5,
    alpha=0.8,
)

ax.set_facecolor("#1e1e2f")
ax.set_title(
    f"Comorbilidades en {tipo_comparacion}", fontsize=16, pad=20, color="white"
)
ax.set_xlabel("Número de Pacientes", fontsize=12, color="white")
ax.set_ylabel("Comorbilidad", fontsize=12, color="white")
for i, bar in enumerate(bars):
    width = bar.get_width()
    label_text = f"{int(width):,} ({df_comorb_plot['Porcentaje'].iloc[i]:.1f}%)"
    ax.text(
        width
        + (
            max(df_comorb_plot["Pacientes"]) * 0.02
        ),
        bar.get_y() + bar.get_height() / 2,
        label_text,
        va="center",
        ha="left",
        color="white",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", fc="#222244", alpha=0.7, ec="gray"),
    )

ax.tick_params(axis="both", colors="white")
ax.grid(axis="x", linestyle="--", alpha=0.3, color="gray")

for spine in ax.spines.values():
    spine.set_edgecolor("gray")
    spine.set_linewidth(0.5)

plt.tight_layout()
# Mostrar gráfico
st.pyplot(fig)

divisor_visual();


# =================== DIVISOR VISUAL ===================
st.markdown(
    """
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución de Casos por Rango de Edad</h3>
</div>
""",
    unsafe_allow_html=True,
)

# Filtrar edades válidas
df_edad = df[df["EDAD"].notna() & (df["EDAD"] >= 0)]

# Definir rangos y etiquetas
bins = list(range(0, 100, 5)) + [150]
labels = [f"{i}-{i+4}" for i in range(0, 95, 5)] + ["95+"]

# Agrupar por rangos
df_edad["RANGO_EDAD"] = pd.cut(df_edad["EDAD"], bins=bins, labels=labels, right=False)

# Contar frecuencias por rango
conteo_rangos = df_edad["RANGO_EDAD"].value_counts().sort_index()

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
fig.patch.set_facecolor("#1e1e2f")
gradient_colors = plt.cm.viridis(np.linspace(0, 0.8, len(conteo_rangos)))
bars = ax.bar(
    range(len(conteo_rangos)),
    conteo_rangos.values,
    color=gradient_colors,
    edgecolor="white",
    linewidth=0.5,
    alpha=0.8,
)

ax.set_facecolor("#1e1e2f")
ax.set_title(
    "Distribución de Casos por Rango de Edad", fontsize=16, pad=20, color="white"
)
ax.set_xlabel("Rango de Edad", fontsize=12, color="white", labelpad=10)
ax.set_ylabel("Número de Casos", fontsize=12, color="white", labelpad=10)
ax.set_xticks(range(len(conteo_rangos)))
ax.set_xticklabels(labels, rotation=45, ha="right", color="white", fontsize=10)
ax.tick_params(axis="y", colors="white", labelsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.3, color="gray")
umbral = (
    max(conteo_rangos) * 0.05
)  # Solo mostrar valores para barras con > 5% del máximo

for i, v in enumerate(conteo_rangos.values):
    if v > umbral:
        ax.text(
            i,
            v + (max(conteo_rangos) * 0.01),
            f"{int(v):,}",
            ha="center",
            va="bottom",
            color="white",
            fontsize=9,
            rotation=0,
            bbox=dict(boxstyle="round,pad=0.3", fc="#222244", alpha=0.7, ec="gray"),
        )
for spine in ax.spines.values():
    spine.set_edgecolor("gray")
    spine.set_linewidth(0.5)

plt.tight_layout()
st.pyplot(fig)


col1, col2, col3 = st.columns(3)

with col1:
    # Encontrar el rango de edad con más casos
    rango_max = conteo_rangos.idxmax()
    max_casos = conteo_rangos.max()
    st.metric("Rango de edad más frecuente", f"{rango_max}", f"{max_casos:,} casos")

with col2:
    # Calcular edad promedio
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
    suma_ponderada = sum(
        rangos_dict[rango] * casos for rango, casos in conteo_rangos.items()
    )
    edad_promedio = suma_ponderada / total_casos if total_casos > 0 else 0

    st.metric(
        "Edad promedio estimada",
        f"{edad_promedio:.1f} años",
        help="Calculado usando el punto medio de cada rango de edad",
    )

with col3:
    # Calcular mediana
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
        help="Rango donde se alcanza el 50% acumulado de casos",
    )
    
divisor_visual();


st.markdown(
    """
<div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
    <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución de Comorbilidades en Pacientes Fallecidos</h3>
</div>
""",
    unsafe_allow_html=True,
)

# Filtrar defunciones válidas
df_def = df[df["FECHA_DEF"].notna() & (df["FECHA_DEF"] != "9999-99-99")].copy()

# Comorbilidades a considerar
cols_comorb = [
    "DIABETES",
    "HIPERTENSION",
    "OBESIDAD",
    "RENAL_CRONICA",
    "CARDIOVASCULAR",
    "EPOC",
    "ASMA",
    "INMUSUPR",
    "TABAQUISMO",
    "OTRA_COM",
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
    "OTRA_COM": "Otras comorbilidades",
}

# Contar cuántos fallecidos tienen cada comorbilidad (valor = 1)
conteo_comorb = {
    nombres_legibles.get(col, col): df_def[df_def[col] == 1].shape[0]
    for col in cols_comorb
    if col in df_def.columns
}

# Quitar comorbilidades con 0 ocurrencias y ordenar por frecuencia descendente
conteo_comorb = dict(
    sorted(
        {k: v for k, v in conteo_comorb.items() if v > 0}.items(),
        key=lambda item: item[1],
        reverse=True,
    )
)

# Total de pacientes fallecidos
total_fallecidos = len(df_def)

# Total de comorbilidades (suma de todas las apariciones)
total_comorbilidades = sum(conteo_comorb.values())

# Calcular porcentajes sobre el total de fallecidos
porcentajes_sobre_fallecidos = {
    k: (v / total_fallecidos) * 100 for k, v in conteo_comorb.items()
}

colors = [
    "#e74c3c",
    "#3498db",
    "#2ecc71",
    "#f39c12",
    "#9b59b6",
    "#1abc9c",
    "#e67e22",
    "#34495e",
    "#7f8c8d",
    "#d35400",
]

plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(10, 8), facecolor="#1e1e2f")
fig.patch.set_facecolor("#1e1e2f")
wedges, texts, autotexts = ax.pie(
    conteo_comorb.values(),
    labels=None,
    autopct="%1.1f%%",
    startangle=90,
    wedgeprops=dict(
        width=0.5, edgecolor="white", linewidth=0.5
    ),
    pctdistance=0.85,
    colors=colors[: len(conteo_comorb)],
)

for autotext in autotexts:
    autotext.set_color("white")
    autotext.set_fontsize(7)
    autotext.set_weight("bold")
centre_circle = plt.Circle((0, 0), 0.35, fc="#1e1e2f")
ax.add_patch(centre_circle)
ax.annotate(
    f"{total_fallecidos:,}\nFallecidos",
    xy=(0, 0),
    ha="center",
    va="center",
    fontsize=14,
    fontweight="bold",
    color="white",
)

ax.legend(
    wedges,
    [f"{k} ({int(v):,})" for k, v in conteo_comorb.items()],
    title="Comorbilidades",
    loc="center left",
    bbox_to_anchor=(1, 0, 0.5, 1),
    frameon=True,
    facecolor="#222244",
    edgecolor="gray",
    fontsize=10,
)
ax.set_title(
    "Comorbilidades en Pacientes Fallecidos", fontsize=16, pad=20, color="white"
)
ax.axis("equal")
fig.text(
    0.5,
    0.02,
    f"* Los porcentajes representan la proporción de cada comorbilidad sobre el total de {total_comorbilidades:,} comorbilidades registradas",
    ha="center",
    color="white",
    fontsize=9,
    alpha=0.7,
)

st.pyplot(fig)

divisor_visual();

col1, col2 = st.columns(2)
with col1:
    st.markdown(
        """
        <div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
            <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Distribución de Intubación por Rangos de Edad</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filtrar solo valores válidos y con fecha
    df_intubado_edad = df[df["INTUBADO"].isin([1, 2]) & df["EDAD"].notna()].copy()

    # Crear rangos de edad
    # Crear bins y etiquetas correctamente (10-intervalos)
    bins = list(range(0, 101, 10)) + [
        120
    ]  # [0,10,20,...,100,120] → 12 valores → 11 intervalos
    labels_rangos = [f"{i}-{i+9}" for i in range(0, 100, 10)] + [
        "100+"
    ]  # solo 11 etiquetas

    df_intubado_edad["RANGO_EDAD"] = pd.cut(
        df_intubado_edad["EDAD"], bins=bins, labels=labels_rangos, right=False
    )
    df_intubado_edad["ESTADO_INTUBADO"] = df_intubado_edad["INTUBADO"].map(
        {1: "Sí", 2: "No"}
    )

    # Agrupar por rango e intubación
    conteo_edad = (
        df_intubado_edad.groupby(["RANGO_EDAD", "ESTADO_INTUBADO"])
        .size()
        .reset_index(name="PACIENTES")
    )

    plt.style.use("dark_background")
    fig1, ax1 = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
    fig1.patch.set_facecolor("#1e1e2f")
    color_intubado_si = "#e74c3c"  # Rojo para intubados
    color_intubado_no = "#2ecc71"  # Verde para no intubados
    bars = sns.barplot(
        data=conteo_edad,
        x="RANGO_EDAD",
        y="PACIENTES",
        hue="ESTADO_INTUBADO",
        palette={"Sí": color_intubado_si, "No": color_intubado_no},
        alpha=0.8,
        ax=ax1,
    )
    ax1.set_facecolor("#1e1e2f")
    ax1.set_title(
        "Pacientes Intubados por Rango de Edad", fontsize=16, pad=20, color="white"
    )
    ax1.set_xlabel("Rango de Edad", fontsize=12, color="white")
    ax1.set_ylabel("Número de Pacientes", fontsize=12, color="white")
    plt.xticks(rotation=45, ha="right", color="white")
    plt.yticks(color="white")
    ax1.grid(axis="y", linestyle="--", alpha=0.3, color="gray")
    legend = ax1.legend(
        title="Estado de Intubación", frameon=True, facecolor="#222244", edgecolor="gray"
    )
    legend.get_title().set_color("white")
    for text in legend.get_texts():
        text.set_color("white")
    for bar in ax1.patches:
        bar.set_edgecolor("white")
        bar.set_linewidth(0.5)
    for spine in ax1.spines.values():
        spine.set_edgecolor("gray")
        spine.set_linewidth(0.5)
    for bar in ax1.patches:
        height = bar.get_height()
        if height > 0:
            if (
                height > max(conteo_edad["PACIENTES"]) * 0.05
            ):
                ax1.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 5,
                    f"{int(height):,}",
                    ha="center",
                    va="bottom",
                    color="white",
                    fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.2", fc="#222244", alpha=0.7, ec="gray"),
                )
    plt.tight_layout()
    st.pyplot(fig1)
# =================== DIVISOR VISUAL ===================
divisor_visual();

# === Gráfico: Días entre inicio de síntomas e ingreso (0–20 días, en pasos de 2) ===
with col2:
    st.markdown(
        """
    <div style="background-color: #1e1e2f; border-radius: 10px; padding: 15px; margin-bottom: 20px;">
        <h3 style="color: #ffffff; margin-top: 0; text-align: center;">Días desde Inicio de Síntomas hasta Ingreso Hospitalario</h3>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Asegurar fechas válidas
    df_fechas = df.copy()
    df_fechas["FECHA_SINTOMAS"] = pd.to_datetime(
        df_fechas["FECHA_SINTOMAS"], errors="coerce"
    )
    df_fechas["FECHA_INGRESO"] = pd.to_datetime(df_fechas["FECHA_INGRESO"], errors="coerce")

    # Calcular diferencia de días
    df_fechas = df_fechas[
        df_fechas["FECHA_SINTOMAS"].notna() & df_fechas["FECHA_INGRESO"].notna()
    ]
    df_fechas["DIFERENCIA_DIAS"] = (
        df_fechas["FECHA_INGRESO"] - df_fechas["FECHA_SINTOMAS"]
    ).dt.days

    # Filtrar días entre 0 y 20
    df_dias = df_fechas[
        (df_fechas["DIFERENCIA_DIAS"] >= 0) & (df_fechas["DIFERENCIA_DIAS"] <= 20)
    ]

    # Bins de 2 en 2
    bins = list(range(0, 22, 2))  # 0–2, 2–4, ..., 20
    labels = [f"{i}-{i+1}" for i in range(0, 20, 2)]

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
    fig.patch.set_facecolor("#1e1e2f")

    color_base = "#3498db"  # Azul para el histograma
    counts, edges, bars = ax.hist(
        df_dias["DIFERENCIA_DIAS"],
        bins=bins,
        edgecolor="white",
        linewidth=0.8,
        color=color_base,
        alpha=0.8,
    )
    ax.set_facecolor("#1e1e2f")
    ax.set_title(
        "Distribución de Días con Síntomas antes del Ingreso Hospitalario",
        fontsize=16,
        pad=20,
        color="white",
    )
    ax.set_xlabel(
        "Días desde inicio de síntomas hasta ingreso",
        fontsize=12,
        color="white",
        labelpad=10,
    )
    ax.set_ylabel("Número de Pacientes", fontsize=12, color="white", labelpad=10)

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{int(x):,}"))

    # Eje X con ticks pares y etiquetas mejoradas
    ax.set_xticks(list(range(0, 21, 2)))  # 0, 2, 4, ..., 20
    ax.tick_params(axis="both", colors="white", labelsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.3, color="gray")

    # Mostrar valores encima de las barras
    for i, (count, bar) in enumerate(zip(counts, bars)):
        height = bar.get_height()
        if height > 0:
            ax.annotate(
                f"{int(count):,}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                color="white",
                bbox=dict(boxstyle="round,pad=0.2", fc="#222244", alpha=0.7, ec="gray"),
            )

    for spine in ax.spines.values():
        spine.set_edgecolor("gray")
        spine.set_linewidth(0.5)

    plt.tight_layout()

    st.pyplot(fig)



st.markdown("## Influencia de Comorbilidades en la Intubación")
# Filtrar pacientes con INTUBADO válido
df_intub = df[df["INTUBADO"].isin([1, 2])].copy()

# Comorbilidades a evaluar
comorbilidades = [
    "DIABETES",
    "HIPERTENSION",
    "OBESIDAD",
    "RENAL_CRONICA",
    "CARDIOVASCULAR",
    "EPOC",
    "ASMA",
    "INMUSUPR",
    "TABAQUISMO",
    "OTRA_COM",
]

# Construcción de tabla
data = []
for col in comorbilidades:
    if col in df_intub.columns:
        total = df_intub[df_intub[col] == 1]
        n_total = len(total)
        n_intub = len(total[total["INTUBADO"] == 1])
        pct = round((n_intub / n_total) * 100, 1) if n_total > 0 else 0
        data.append(
            {
                "Comorbilidad": col,
                "Total con comorbilidad": n_total,
                "Intubados": n_intub,
                "% Intubados": pct,
            }
        )

# Crear DataFrame y ordenar por % Intubados DESC
df_result = pd.DataFrame(data).sort_values(by="% Intubados", ascending=False)
df_result = df_result.reset_index(drop=True)

# En lugar de usar .style.format(), formatee los valores directamente en el DataFrame
df_result["Total con comorbilidad"] = df_result["Total con comorbilidad"].apply(
    lambda x: f"{x:,}"
)
df_result["Intubados"] = df_result["Intubados"].apply(lambda x: f"{x:,}")
df_result["% Intubados"] = df_result["% Intubados"].apply(lambda x: f"{x:.1f} %")

# Mostrar con st.table() que aplica un estilo predefinido
st.table(df_result)
