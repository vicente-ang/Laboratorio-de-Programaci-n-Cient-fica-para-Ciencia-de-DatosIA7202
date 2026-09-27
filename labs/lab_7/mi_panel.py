"""Andamiaje del panel de la Parte 2. Renómbrenlo si quieren.

MATERIAL PROVISTO. Lo que ya está escrito acá —los imports, la configuración
de la página y el cargador de datos— es infraestructura y no se evalúa: son
las mismas líneas para cualquier panel sobre este dataset. Lo que sí se evalúa
son las cuatro secciones de más abajo.

Las secciones están en un orden que funciona, pero no es obligatorio:
reordenarlas o renombrarlas no descuenta. Lo que se corrige es que las cuatro
cosas estén y que cada gráfico explique por qué está ahí.

Para trabajar:

    uv run streamlit run mi_panel.py

Streamlit reejecuta el archivo completo cada vez que alguien mueve un control,
así que el navegador se actualiza solo al guardar.
"""

from pathlib import Path

import plotly.express as px
import polars as pl
import streamlit as st

RUTA_DATOS = Path(__file__).parent / "data" / "raw" / "penguins.csv"

st.set_page_config(
    page_title="Pingüinos de Palmer", page_icon="🐧", layout="wide"
)
st.title("🐧 Pingüinos del archipiélago de Palmer")


@st.cache_data
def cargar_datos() -> pl.DataFrame:
    """Lee el CSV sin modificarlo.

    `null_values=["NA"]` es necesario: el archivo viene de R, donde `NA` marca
    los faltantes. Sin ese argumento, polars lee las columnas numéricas como
    texto. Con él, los nulos quedan adentro — que es lo que queremos, porque
    este laboratorio no limpia nada.
    """
    return pl.read_csv(RUTA_DATOS, null_values=["NA"])


df = cargar_datos()


# --- 1) La tabla interactiva -----------------------------------------------
#
# Una tabla con el dataset que el lector pueda ordenar por cualquier columna y
# filtrar con al menos dos controles: uno categórico y uno de rango numérico.
# Esos mismos filtros deben afectar también a los cuatro gráficos. Los
# registros sin valor en la columna del filtro numérico quedan fuera de la
# selección filtrada. Si ningún registro cumple los filtros, muestren un aviso.
#
# Ordenar y buscar los trae `st.dataframe` de fábrica, sin programar nada.
# Filtrar no: los controles devuelven la selección y ustedes filtran el
# DataFrame antes de pasárselo a la tabla. Denle formato a las columnas, que
# `flipper_length_mm` no es un encabezado para mostrarle a un cliente.
#
#   https://docs.streamlit.io/develop/api-reference/data/st.dataframe
#   https://docs.streamlit.io/develop/api-reference/data/st.column_config
#   https://docs.streamlit.io/develop/api-reference/widgets/st.multiselect
#   https://docs.streamlit.io/develop/api-reference/widgets/st.slider

# Su código aquí

st.sidebar.header("Filtros")

# Filtro categórico: especie
especies = sorted(df["species"].unique().to_list())

especies_seleccionadas = st.sidebar.multiselect(
    "Especie", options=especies, default=especies
)

# Filtro numérico: masa corporal
masa_min = int(df["body_mass_g"].drop_nulls().min())
masa_max = int(df["body_mass_g"].drop_nulls().max())

rango_masa = st.sidebar.slider(
    "Masa corporal (g)",
    min_value=masa_min,
    max_value=masa_max,
    value=(masa_min, masa_max),
    step=50,
)


df_filtrado = df.filter(
    pl.col("species").is_in(especies_seleccionadas)
    & pl.col("body_mass_g").is_not_null()
    & pl.col("body_mass_g").is_between(rango_masa[0], rango_masa[1])
)

st.subheader("Datos filtrados")

if df_filtrado.is_empty():
    st.warning("No hay registros que cumplan con los filtros seleccionados.")


st.dataframe(
    df_filtrado,
    width="stretch",
    hide_index=True,
    column_config={
        "species": st.column_config.TextColumn("Especie"),
        "island": st.column_config.TextColumn("Isla"),
        "culmen_length_mm": st.column_config.NumberColumn(
            "Largo del pico (mm)"
        ),
        "culmen_depth_mm": st.column_config.NumberColumn(
            "Profundidad del pico (mm)"
        ),
        "flipper_length_mm": st.column_config.NumberColumn(
            "Largo de aleta (mm)"
        ),
        "body_mass_g": st.column_config.NumberColumn("Masa corporal (g)"),
        "sex": st.column_config.TextColumn("Sexo"),
    },
)


# --- 2) La calidad de los datos --------------------------------------------
#
# Un informe visible en la página, calculado sobre el CSV completo aunque se
# apliquen filtros: qué columnas tienen nulos y cuántos, cuál es el valor
# inesperado de `sex` y cómo pueden afectar esos problemas los recuentos,
# filtros o gráficos del panel.
#
# Las cifras se calculan desde `df`, no se escriben a mano: si el
# archivo cambiara, un número escrito a mano queda mintiendo.
#
#   https://docs.streamlit.io/develop/api-reference/status/st.warning

# Su código aquí

st.header("Calidad de los datos")

# Cantidad de nulos por columna
nulos = (
    df.null_count()
    .transpose(
        include_header=True,
        header_name="Columna",
        column_names=["Cantidad de nulos"],
    )
    .filter(pl.col("Cantidad de nulos") > 0)
)

st.subheader("Valores faltantes")

st.dataframe(
    nulos,
    width="stretch",
    hide_index=True,
)

# Valores inesperados en la variable sex
sex_inesperado = (
    df.filter(
        pl.col("sex").is_not_null() & ~pl.col("sex").is_in(["MALE", "FEMALE"])
    )
    .select("sex")
    .unique()
)

st.subheader("Valores inesperados")

if sex_inesperado.height > 0:
    valores = sex_inesperado["sex"].to_list()

    st.warning(
        f"La variable `sex` contiene valores inesperados: {', '.join(valores)}."
    )
else:
    st.success("No se encontraron valores inesperados en la variable `sex`.")

st.write(
    "Los valores nulos pueden hacer que algunas observaciones no aparezcan "
    "en ciertos gráficos o filtros, dependiendo de las variables utilizadas. "
    "Además, un valor inesperado en `sex` podría generar una categoría "
    "adicional y alterar los recuentos si se utiliza esta variable."
)


# --- 3) Los cuatro gráficos ------------------------------------------------
#
# Cuatro gráficos a elección, de al menos dos tipos distintos. Pueden reusar
# los de la Parte 1 o construir otros. Van a necesitar `plotly.express`:
# impórtenlo arriba, con el resto.
#
# Cada gráfico lleva, JUNTO A ÉL Y VISIBLE EN LA PÁGINA, por qué esa
# información es útil y por qué eligieron esa visualización. Un comentario en
# el código no cuenta: quien abre el panel no lee el código.
#
#   https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
#   https://docs.streamlit.io/develop/api-reference/text/st.caption
#   https://docs.streamlit.io/develop/api-reference/layout/st.columns

# Su código aquí

st.header("Visualizaciones")

if df_filtrado.is_empty():
    st.warning(
        "No hay datos suficientes para mostrar los gráficos "
        "con los filtros seleccionados."
    )

else:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Masa corporal y largo de aleta")

        st.caption(
            "Este gráfico permite observar si existe una relación entre "
            "el largo de las aletas y la masa corporal, además de comparar "
            "las especies. Se utiliza un gráfico de dispersión porque ambas "
            "variables son numéricas y permite ver su relación."
        )

        fig_dispersion = px.scatter(
            df_filtrado,
            x="flipper_length_mm",
            y="body_mass_g",
            color="species",
            labels={
                "flipper_length_mm": "Largo de aleta (mm)",
                "body_mass_g": "Masa corporal (g)",
                "species": "Especie",
            },
            title="Relación entre largo de aleta y masa corporal",
        )

        st.plotly_chart(
            fig_dispersion,
            width="stretch",
        )

    with col2:
        st.subheader("Masa corporal según especie")

        st.caption(
            "Este gráfico permite comparar la distribución de la masa "
            "corporal entre las distintas especies. Se utiliza un boxplot "
            "porque muestra la mediana, dispersión y posibles valores extremos."
        )

        fig_box = px.box(
            df_filtrado,
            x="species",
            y="body_mass_g",
            color="species",
            labels={
                "species": "Especie",
                "body_mass_g": "Masa corporal (g)",
            },
            title="Distribución de la masa corporal por especie",
        )

        st.plotly_chart(
            fig_box,
            width="stretch",
        )

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Distribución del largo de las aletas")

        st.caption(
            "Este gráfico permite observar en qué valores se concentra "
            "el largo de las aletas y cómo cambia entre especies. "
            "Se utiliza un histograma porque permite visualizar la "
            "distribución de una variable numérica."
        )

        fig_histograma = px.histogram(
            df_filtrado,
            x="flipper_length_mm",
            color="species",
            nbins=20,
            barmode="overlay",
            labels={
                "flipper_length_mm": "Largo de aleta (mm)",
                "species": "Especie",
            },
            title="Distribución del largo de las aletas",
        )

        st.plotly_chart(
            fig_histograma,
            width="stretch",
        )

    with col4:
        st.subheader("Cantidad de pingüinos por isla")

        st.caption(
            "Este gráfico permite comparar cuántos registros corresponden "
            "a cada isla dentro de la selección actual. Se utiliza un gráfico "
            "de barras porque facilita la comparación entre categorías."
        )

        conteo_islas = (
            df_filtrado.group_by("island")
            .len()
            .rename({"len": "cantidad"})
            .sort("cantidad", descending=True)
        )

        fig_barras = px.bar(
            conteo_islas,
            x="island",
            y="cantidad",
            labels={
                "island": "Isla",
                "cantidad": "Cantidad de pingüinos",
            },
            title="Cantidad de pingüinos por isla",
        )

        st.plotly_chart(
            fig_barras,
            width="stretch",
        )


# --- 4) El tema --------------------------------------------------------------
#
# Este no se programa acá: vive en `.streamlit/config.toml`, al lado de este
# archivo. Ya existe, con las claves comentadas — descoméntenlas y decidan sus
# colores.
#
# Para comprobar que el suyo está haciendo algo: renombren el archivo,
# reinicien el panel y vean si cambia. Si no cambia, no lo configuraron.
#
#   https://docs.streamlit.io/develop/concepts/configuration/theming
