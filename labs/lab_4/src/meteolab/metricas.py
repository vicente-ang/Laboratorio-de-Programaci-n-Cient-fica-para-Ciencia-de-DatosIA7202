"""Agregaciones sobre las temperaturas medias mensuales."""

from __future__ import annotations

import polars as pl

Tabla = pl.DataFrame | pl.LazyFrame


def _filtrar_paises(
    mensuales: Tabla,
    paises: list[str] | tuple[str, ...] | None,
) -> Tabla:
    if paises is None:
        return mensuales
    return mensuales.filter(pl.col("iso_alpha3").is_in(paises))


def resumen_mensual(
    mensuales: Tabla,
    paises: list[str] | tuple[str, ...] | None = None,
) -> Tabla:
    """Calcula la climatología mensual por país."""
    datos = _filtrar_paises(mensuales, paises)
    return (
        datos.group_by("iso_alpha3", "country", "month")
        .agg(
            pl.len().alias("observaciones"),
            pl.col("temperature_c").mean().round(2).alias("temperature_mean"),
        )
        .sort("iso_alpha3", "month")
    )


def resumen_anual_desde_mensuales(
    mensuales: Tabla,
    paises: list[str] | tuple[str, ...] | None = None,
) -> Tabla:
    """Calcula medias anuales usando únicamente filas mensuales."""
    datos = _filtrar_paises(mensuales, paises)
    return (
        datos.group_by("iso_alpha3", "country", "year")
        .agg(
            pl.len().alias("meses_disponibles"),
            pl.col("temperature_c").mean().round(2).alias("temperature_mean"),
        )
        .sort("iso_alpha3", "year")
    )


def anomalias_mensuales(
    mensuales: Tabla,
    umbral: float = 2.0,
) -> Tabla:
    """Marca anomalías usando una ventana por país y mes."""
    grupos = ["iso_alpha3", "month"]
    con_referencia = mensuales.with_columns(
        pl.col("temperature_c")
        .mean()
        .over(grupos)
        .alias("temperature_mean_month"),
        pl.col("temperature_c")
        .std()
        .over(grupos)
        .alias("_temperature_std_month"),
    )
    con_anomalia = con_referencia.with_columns(
        pl.when(
            pl.col("_temperature_std_month").is_not_null()
            & (pl.col("_temperature_std_month") != 0)
        )
        .then(
            (pl.col("temperature_c") - pl.col("temperature_mean_month"))
            / pl.col("_temperature_std_month")
        )
        .otherwise(0.0)
        .alias("standardized_anomaly")
    )
    return con_anomalia.with_columns(
        (pl.col("standardized_anomaly").abs() > umbral)
        .fill_null(False)
        .alias("is_anomaly")
    ).drop("_temperature_std_month")
