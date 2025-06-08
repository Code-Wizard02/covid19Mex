# COVID19 MEXICO DASHBOARD

## Código de Activación del Ambiente Virtual
```bash
.\covid19\Scripts\activate
```

## Código de Inicio de Streamlit

```bash
python -m streamlit run .\covid19Mexico.py
```

# Documentación del Dashboard COVID-19

```markdown
# Dashboard COVID-19 - Documentación Técnica

Este documento explica en detalle el código de un dashboard interactivo para visualizar datos de COVID-19, construido con Streamlit y conectado a una base de datos MySQL.

## Índice
1. [Importación de librerías](#1-importación-de-librerías)
2. [Conexión a MySQL](#2-conexión-a-mysql)
3. [Carga de datos](#3-carga-de-datos)
4. [Configuración inicial de Streamlit](#4-configuración-inicial-de-streamlit)
5. [Filtros y selección de datos](#5-filtros-y-selección-de-datos)
6. [KPIs y visualizaciones](#6-kpis-y-visualizaciones)
7. [Gráficos principales](#7-gráficos-principales)
8. [Análisis demográficos](#8-análisis-demográficos)
9. [Visualización de comorbilidades](#9-visualización-de-comorbilidades)
10. [Análisis temporales](#10-análisis-temporales)

---

## 1. Importación de librerías

```python
import streamlit as st
import pandas as pd
import pymysql
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
```

- **Streamlit**: Framework para crear aplicaciones web interactivas
- **Pandas**: Manipulación y análisis de datos
- **PyMySQL**: Conexión con bases de datos MySQL
- **Matplotlib/Seaborn**: Visualización de datos
- **NumPy**: Operaciones numéricas

## 2. Conexión a MySQL

```python
def get_mysql_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="password",
        database="covid19",
        cursorclass=pymysql.cursors.Cursor,
    )
```

Esta función establece la conexión con la base de datos MySQL especificando:
- Host local
- Credenciales de acceso
- Base de datos "covid19"
- Tipo de cursor para operaciones

## 3. Carga de datos

```python
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
```

Características clave:
- Usa `@st.cache_data` para cachear los datos y mejorar rendimiento
- Manejo de errores con try-except
- Cierra la conexión en el bloque `finally`
- Retorna un DataFrame de Pandas con los datos

## 4. Configuración inicial de Streamlit

```python
tablas = {
    "2020": "covid19_2020",
    "2021": "covid19_2021",
    "2022": "covid19_2022",
    "2023": "covid19_2023",
}

st.title("Dashboard de Datos COVID 19")
st.sidebar.header("Parámetros")
seleccion = st.sidebar.selectbox("Selecciona el año", list(tablas.keys()))
```

- Mapeo de años a tablas en la base de datos
- Título principal del dashboard
- Selector de año en la barra lateral

## 5. Filtros y selección de datos

```python
if "cache_dfs" not in st.session_state:
    st.session_state.cache_dfs = {}

if seleccion not in st.session_state.cache_dfs:
    st.session_state.cache_dfs[seleccion] = load_table_cached(tablas[seleccion])

df = st.session_state.cache_dfs[seleccion]
```

Lógica de caché:
- Usa `st.session_state` para mantener los DataFrames cargados
- Solo carga datos si no están ya en caché

Filtros adicionales:
```python
regiones = df["REGION"].dropna().unique()
region_seleccionada = st.sidebar.selectbox("Selecciona una Región", sorted(regiones))

entidades = df[df["REGION"] == region_seleccionada]["ENTIDAD"].dropna().unique()
entidad_seleccionada = st.sidebar.selectbox("Selecciona una Entidad Federativa", sorted(entidades))

df_filtrado = df[(df["REGION"] == region_seleccionada) & (df["ENTIDAD"] == entidad_seleccionada)]
```

## 6. KPIs y visualizaciones

Los KPIs se muestran usando tarjetas personalizadas con CSS:

```python
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
...
</style>
""", unsafe_allow_html=True)
```

KPIs calculados:
- Casos confirmados, negativos, sospechosos
- Defunciones y recuperados
- Distribución por género
- Porcentaje de hospitalizados/ambulatorios

## 7. Gráficos principales

### 7.1 Distribución Demográfica por Edad y Sexo

```python
# Preparación de datos
df_tipo = df[df["CLASIFICACION_FINAL"] == tipo_valor].copy()
df_tipo["RANGO_EDAD"] = pd.cut(df_tipo["EDAD"], bins=bins, labels=labels, right=False)
df_tipo["SEXO"] = df_tipo["SEXO"].map({1: "Hombres", 2: "Mujeres"})

# Gráfico con Seaborn
fig, ax = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
sns.barplot(data=conteo, x="RANGO_EDAD", y="CASOS", hue="SEXO", 
           palette={"Hombres": "#3498db", "Mujeres": "#e74c3c"}, alpha=0.8, ax=ax)
```

### 7.2 Distribución por Edad y Tipo de Atención

Similar al anterior pero agrupando por tipo de paciente (hospitalizado/ambulatorio)

## 8. Análisis demográficos

### 8.1 Gráfico de pastel: Comorbilidades

```python
wedges, texts, autotexts = ax_pie.pie(
    porcentajes.values(),
    labels=None,
    autopct="%1.1f%%",
    startangle=90,
    wedgeprops=dict(width=0.5, edgecolor="white", linewidth=0.5),
    colors=colors[: len(porcentajes)],
)
```

### 8.2 Histograma de distribución por edad

```python
df_edad["RANGO_EDAD"] = pd.cut(df_edad["EDAD"], bins=bins, labels=labels, right=False)
conteo_rangos = df_edad["RANGO_EDAD"].value_counts().sort_index()
```

## 9. Visualización de comorbilidades

### 9.1 Barras horizontales de comorbilidades

```python
df_comorb_plot = pd.DataFrame({"Pacientes": frecuencias, "Porcentaje": porcentajes})
df_comorb_plot = df_comorb_plot.sort_values(by="Pacientes", ascending=True)

bars = ax.barh(
    df_comorb_plot.index,
    df_comorb_plot["Pacientes"],
    color=colors,
    edgecolor="white",
    linewidth=0.5,
    alpha=0.8,
)
```

## 10. Análisis temporales

### 10.1 Evolución mensual de pacientes intubados

```python
df_intubado["MES"] = df_intubado["FECHA_INGRESO"].dt.month
conteo_intubado = df_intubado.groupby(["MES", "INTUBADO"]).size().reset_index(name="PACIENTES")
```

### 10.2 Días desde síntomas hasta ingreso

```python
df_fechas["DIFERENCIA_DIAS"] = (df_fechas["FECHA_INGRESO"] - df_fechas["FECHA_SINTOMAS"]).dt.days
df_dias = df_fechas[(df_fechas["DIFERENCIA_DIAS"] >= 0) & (df_fechas["DIFERENCIA_DIAS"] <= 20)]
```

## 11. Detalles Técnicos Adicionales

### 11.1 Manejo de Datos Faltantes

El código incluye tratamiento robusto para valores faltantes:

```python
# Ejemplo en filtrado de regiones
regiones = df["REGION"].dropna().unique()  # Elimina valores NaN antes de obtener valores únicos

# Ejemplo en cálculo de defunciones
defunciones = df_confirmados[
    df_confirmados["FECHA_DEF"].notna() & (df_confirmados["FECHA_DEF"] != "9999-99-99")
]
```

### 11.2 Transformación de Datos

Varias transformaciones clave se aplican:

```python
# Convertir fechas
df["FECHA_INGRESO"] = pd.to_datetime(df["FECHA_INGRESO"], errors="coerce")

# Mapeo de valores numéricos a categóricos
df_tipo["SEXO"] = df_tipo["SEXO"].map({1: "Hombres", 2: "Mujeres"})

# Creación de rangos de edad
bins = list(range(0, 100, 5)) + [100]
labels = [f"{i}-{i+4}" for i in range(0, 95, 5)] + ["95+"]
df["RANGO_EDAD"] = pd.cut(df["EDAD"], bins=bins, labels=labels, right=False)
```

### 11.3 Optimización de Rendimiento

Técnicas utilizadas:

1. **Caché de Streamlit**:
   ```python
   @st.cache_data(show_spinner="Cargando datos desde MySQL...")
   def load_table_cached(table_name):
       # ...
   ```

2. **Manejo de sesión**:
   ```python
   if "cache_dfs" not in st.session_state:
       st.session_state.cache_dfs = {}
   ```

3. **Filtrado temprano**:
   ```python
   df_filtrado = df[
       (df["REGION"] == region_seleccionada) & 
       (df["ENTIDAD"] == entidad_seleccionada)
   ]
   ```

## 12. Estructura del Proyecto

La lógica sigue un flujo claro:

1. **Carga de datos**:
   - Conexión a MySQL
   - Carga con caché
   - Almacenamiento en session_state

2. **Configuración UI**:
   - Diseño sidebar/tabs
   - Selectores de filtros
   - Estilos CSS personalizados

3. **Procesamiento**:
   - Filtrado por selecciones
   - Cálculo de métricas
   - Transformación para visualizaciones

4. **Visualización**:
   - KPIs con formato
   - Gráficos Matplotlib/Seaborn
   - Secciones organizadas

## 13. Análisis de Código por Componentes

### 13.1 Componente de KPIs

```python
# Configuración de colores
color_confirmados = "#e74c3c"
color_negativos = "#3498db"
color_sospechosos = "#f39c12"

# Función de formato
def format_number(num):
    return f"{num:,}".replace(",", ",")  # Formato con separadores de miles

# Ejemplo de KPI
st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-left-border" style="background-color: {color_confirmados};"></div>
    <div class="kpi-icon"><i class="fas fa-virus"></i></div>
    <div class="kpi-title">CONFIRMADOS</div>
    <div class="kpi-value">{format_number(total_confirmados)}</div>
    <div class="kpi-subtitle">Casos acumulados</div>
</div>
""", unsafe_allow_html=True)
```

### 13.2 Componente de Gráficos

Estructura típica de gráficos:

1. **Preparación de datos**:
   ```python
   conteo = df_tipo.groupby(["RANGO_EDAD", "SEXO"]).size().reset_index(name="CASOS")
   ```

2. **Configuración de figura**:
   ```python
   plt.style.use("dark_background")
   fig, ax = plt.subplots(figsize=(14, 7), facecolor="#1e1e2f")
   fig.patch.set_facecolor("#1e1e2f")
   ```

3. **Creación del gráfico**:
   ```python
   sns.barplot(data=conteo, x="RANGO_EDAD", y="CASOS", hue="SEXO",
              palette={"Hombres": color_hombres, "Mujeres": color_mujeres},
              alpha=0.8, ax=ax)
   ```

4. **Personalización**:
   ```python
   ax.set_title(f"Distribución por Edad y Sexo - {tipo_caso}", fontsize=16)
   ax.grid(axis="y", linestyle="--", alpha=0.3, color="gray")
   ```

5. **Renderizado**:
   ```python
   st.pyplot(fig)
   ```

## 14. Manejo de Errores

El código incluye varios mecanismos:

1. **Try-Except en carga de datos**:
   ```python
   try:
       connection = get_mysql_connection()
       # Operaciones con BD
   except Exception as e:
       st.error(f"Error al cargar {table_name}: {e}")
       return pd.DataFrame()
   ```

2. **Verificación de DataFrames vacíos**:
   ```python
   if not df.empty:
       # Procesar datos
   else:
       st.warning("La tabla está vacía o ocurrió un error al cargar los datos.")
   ```

3. **Validación de columnas**:
   ```python
   if col in df_confirmados.columns:
       return round((len(df_confirmados[df_confirmados[col] == 1]) / total_confirmados) * 100, 1)
   ```

## 15. Personalización Visual

### 15.1 Temas y Colores

Paleta de colores principal:
```python
color_palette = {
    "confirmados": "#e74c3c",
    "negativos": "#3498db",
    "sospechosos": "#f39c12",
    "defunciones": "#7f8c8d",
    "recuperados": "#2ecc71",
    "hombres": "#3498db",
    "mujeres": "#e74c3c"
}
```

### 15.2 Estilos CSS

Incluye:
- Tarjetas KPI con bordes laterales
- Gráficos con fondo oscuro
- Tooltips y hover effects
- Diseño responsive

```python
st.markdown("""
<style>
    /* Efecto hover para tarjetas */
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    /* Ajustes para móviles */
    @media (max-width: 600px) {
        .kpi-card {
            padding: 10px;
            min-height: 80px;
        }
    }
</style>
""", unsafe_allow_html=True)
```

## 16. Funcionalidades Interactivas

### 16.1 Selectores Dinámicos

```python
# Selector de año (afecta carga inicial)
seleccion = st.sidebar.selectbox("Selecciona el año", list(tablas.keys()))

# Selector de región (depende del año)
regiones = df["REGION"].dropna().unique()
region_seleccionada = st.sidebar.selectbox("Selecciona una Región", sorted(regiones))

# Selector de entidad (depende de región)
entidades = df[df["REGION"] == region_seleccionada]["ENTIDAD"].dropna().unique()
entidad_seleccionada = st.sidebar.selectbox("Selecciona una Entidad Federativa", sorted(entidades))
```

### 16.2 Botón de Actualización

```python
if st.sidebar.button("Actualizar datos"):
    if "cache_dfs" in st.session_state:
        del st.session_state.cache_dfs[seleccion]
    st.cache_data.clear()
```

## 17. Mejoras Potenciales

1. **Separación en módulos**:
   - `data_loading.py`: Conexión y carga de datos
   - `visualizations.py`: Funciones de gráficos
   - `app.py`: Lógica principal de Streamlit

2. **Tests automatizados**:
   ```python
   def test_data_loading():
       df = load_table_cached("covid19_2020")
       assert not df.empty, "El DataFrame no debe estar vacío"
       assert "REGION" in df.columns, "Debe contener columna REGION"
   ```

3. **Documentación adicional**:
   - Docstrings para funciones clave
   - Guía de estilo del código
   - README con requisitos y configuración

## 18. Conclusión Final

Este dashboard representa una solución completa para:

1. **Integración con BD**: Conexión segura a MySQL con manejo de errores
2. **Procesamiento eficiente**: Transformaciones complejas con Pandas
3. **Visualización profesional**: Gráficos temáticos y KPIs interactivos
4. **Arquitectura escalable**: Organización que permite añadir nuevas funcionalidades

Los puntos clave de implementación incluyen:
- Uso de sesiones para estado persistente
- Cache inteligente para mejorar rendimiento
- Diseño visual cohesivo
- Jerarquía clara de información
- Interactividad bien diseñada

El código sigue mejores prácticas de desarrollo y podría extenderse fácilmente para incluir:
- Exportación de reportes
- Paneles administrativos
- Alertas basadas en umbrales
- Integración con APIs externas