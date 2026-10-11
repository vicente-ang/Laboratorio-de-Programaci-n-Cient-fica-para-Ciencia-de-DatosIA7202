"""Transformaciones de la tabla de mediciones de biomasa."""

import polars as pl

from src.pasturecam.contratos import OBJETIVOS

# Columnas que cambian entre las cinco filas de una misma imagen: no pueden
# formar parte del índice del pivote, o esas filas nunca se juntarían.
COLUMNAS_POR_OBJETIVO = ("sample_id", "target_name", "target")


def a_formato_ancho(df_largo: pl.DataFrame) -> pl.DataFrame:
    """Pivotea la tabla de mediciones de formato largo a ancho.

    `df_largo` trae una fila por imagen y objetivo: `target_name` nombra el
    objetivo, `target` trae su valor, `sample_id` identifica esa fila
    (imagen + objetivo) y el resto de las columnas (incluido `image_path`)
    se repite igual en las cinco filas de una misma imagen. El resultado
    trae una fila por imagen, con una columna por cada nombre de
    `OBJETIVOS` y los metadatos conservados sin duplicar.
    """
    indice = [c for c in df_largo.columns if c not in COLUMNAS_POR_OBJETIVO]
    # Sin `aggregate_function`, `pivot` falla si dos filas comparten índice y
    # objetivo: preferimos un error a promediar mediciones en silencio.
    ancho = df_largo.pivot(on="target_name", index=indice, values="target")
    return ancho.select(*indice, *OBJETIVOS)
