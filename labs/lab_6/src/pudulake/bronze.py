"""Ingesta reproducible de las fuentes Parquet hacia Bronze."""

from __future__ import annotations

from pathlib import Path

import polars as pl

SOURCE_FILES: dict[str, str] = {
    "orders": "orders.parquet",
    "customers": "customers.parquet",
    "order_items": "order_items.parquet",
    "payments": "payments.parquet",
}


def read_sources(raw_dir: Path) -> dict[str, pl.DataFrame]:
    """Lee las cuatro fuentes crudas y conserva exactamente su esquema.

    Bronze no renombra, reordena ni tipa columnas: registra cada fuente tal
    como llegó para poder volver al origen ante cualquier contradicción.
    """
    raw_dir = Path(raw_dir)
    missing = sorted(
        name
        for name, filename in SOURCE_FILES.items()
        if not (raw_dir / filename).is_file()
    )
    if missing:
        raise FileNotFoundError(
            f"Bronze no encontró las fuentes {', '.join(missing)} en {raw_dir}."
        )
    return {
        name: pl.read_parquet(raw_dir / filename)
        for name, filename in SOURCE_FILES.items()
    }
