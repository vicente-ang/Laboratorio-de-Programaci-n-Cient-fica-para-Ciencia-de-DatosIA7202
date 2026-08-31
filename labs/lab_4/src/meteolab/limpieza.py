"""Funciones para revisar nulos y claves temporales."""

from __future__ import annotations

import polars as pl

from src.meteolab.constantes import PERIODOS_MENSUALES, Tabla


def resumen_de_nulos(temperaturas: pl.DataFrame) -> pl.DataFrame:
    """Devuelve conteos y porcentajes de nulos por columna."""
    nulos = pl.DataFrame(
        {
            "columna": temperaturas.columns,
            "nulos": [
                temperaturas[columna].null_count()
                for columna in temperaturas.columns
            ],
        }
    )
    denominador = temperaturas.height or 1
    return nulos.with_columns(
        (pl.col("nulos") / denominador * 100).round(2).alias("porcentaje")
    )


def claves_repetidas(temperaturas: Tabla) -> Tabla:
    """Cuenta repeticiones de país, año y periodo."""
    return (
        temperaturas.group_by("iso_alpha3", "year", "period")
        .len()
        .filter(pl.col("len") > 1)
        .sort("iso_alpha3", "year", "period")
    )


def limpiar_temperaturas(temperaturas: Tabla) -> Tabla:
    """Conserva el contrato de periodos y los nulos válidos."""
    return temperaturas.filter(
        pl.col("period").is_in(PERIODOS_MENSUALES)
        & pl.col("temperature_c").is_not_null()
    )
