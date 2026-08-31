"""Funciones para declarar y validar el esquema CRU."""

from __future__ import annotations

import pandera.errors as pa_errors
import pandera.polars as pa
import polars as pl

from src.meteolab.constantes import ESQUEMA_CRU, PERIODOS_VALIDOS

ESQUEMA_TEMPERATURAS = pa.DataFrameSchema(
    {
        "country": pa.Column(pl.String),
        "iso_alpha2": pa.Column(pl.String),
        "iso_alpha3": pa.Column(pl.String),
        "year": pa.Column(
            pl.Int64,
            checks=[pa.Check.ge(1901), pa.Check.le(2025)],
        ),
        "period": pa.Column(
            pl.String,
            checks=pa.Check.isin(PERIODOS_VALIDOS),
        ),
        "temperature_c": pa.Column(pl.Float64, nullable=True),
        "parameter": pa.Column(
            pl.String,
            checks=pa.Check.equal_to("Mean Temperature"),
        ),
        "units": pa.Column(
            pl.String,
            checks=pa.Check.equal_to("degrees Celsius"),
        ),
        "source_file": pa.Column(pl.String),
    },
    strict=True,
)


def comparar_esquema(temperaturas: pl.DataFrame) -> list[str]:
    """Devuelve diferencias entre el esquema real y el esperado."""
    diferencias: list[str] = []
    esquema_real = temperaturas.schema

    for columna, tipo_esperado in ESQUEMA_CRU.items():
        if columna not in esquema_real:
            diferencias.append(f"Falta la columna '{columna}'.")
            continue
        tipo_real = esquema_real[columna]
        if tipo_real != tipo_esperado:
            diferencias.append(
                f"{columna}: tipo {tipo_real}, se esperaba {tipo_esperado}."
            )

    return diferencias


def validar_esquema(temperaturas: pl.DataFrame) -> None:
    """Comprueba los nombres y tipos de las columnas."""
    diferencias = comparar_esquema(temperaturas)
    if diferencias:
        detalle = " ".join(diferencias)
        raise ValueError(f"Esquema inválido. {detalle}")


def validar_datos(temperaturas: pl.DataFrame) -> pl.DataFrame:
    """Valida tipos, periodos, unidades y valores faltantes."""
    validar_esquema(temperaturas)
    try:
        return ESQUEMA_TEMPERATURAS.validate(temperaturas, lazy=True)
    except pa_errors.SchemaErrors as error:
        raise ValueError(
            f"Los datos no cumplen el contrato: {error.failure_cases}"
        ) from error


def casos_que_fallan(temperaturas: pl.DataFrame) -> pl.DataFrame:
    """Devuelve los incumplimientos sin ocultar sus columnas."""
    try:
        ESQUEMA_TEMPERATURAS.validate(temperaturas, lazy=True)
    except pa_errors.SchemaErrors as error:
        return error.failure_cases

    return pl.DataFrame(
        schema={
            "failure_case": pl.String,
            "schema_context": pl.String,
            "column": pl.String,
            "check": pl.String,
        }
    )
