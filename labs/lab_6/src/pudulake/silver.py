"""Transformaciones y reglas críticas de las entidades Silver."""

from __future__ import annotations

import polars as pl

from src.pudulake.contracts import ContractViolation

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

ORDER_TIMESTAMPS = (
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
)

ALLOWED_ORDER_STATUSES = frozenset(
    {
        "approved",
        "canceled",
        "created",
        "delivered",
        "invoiced",
        "processing",
        "shipped",
        "unavailable",
    }
)

CUSTOMER_COLUMNS = ("customer_id", "customer_unique_id")
ITEM_AMOUNTS = ("price", "freight_value")
PAYMENT_AMOUNTS = ("payment_value",)


def _require_columns(
    frame: pl.DataFrame, table: str, columns: tuple[str, ...]
) -> None:
    """Detiene Silver si la fuente Bronze no trae una columna esperada."""
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ContractViolation(
            f"{table} no recibió las columnas {', '.join(missing)} desde "
            "Bronze."
        )


def _parse_timestamp(dtype: pl.DataType, column: str) -> pl.Expr:
    """Devuelve la expresión que tipa una columna de fecha a ``Datetime``."""
    if dtype.base_type() == pl.Datetime:
        return pl.col(column)
    return (
        pl.col(column)
        .cast(pl.String)
        .str.strptime(pl.Datetime, format=TIMESTAMP_FORMAT, strict=False)
        .alias(column)
    )


def _reject_unparsed_timestamps(
    source: pl.DataFrame, typed: pl.DataFrame
) -> None:
    """Distingue una ausencia real de un texto que no representa una fecha."""
    presence = source.select(
        pl.col(column).is_not_null().alias(f"{column}__present")
        for column in ORDER_TIMESTAMPS
    )
    failure = typed.select(
        pl.col(column).is_null().alias(f"{column}__failed")
        for column in ORDER_TIMESTAMPS
    )
    counts = (
        presence.hstack(failure)
        .select(
            (pl.col(f"{column}__present") & pl.col(f"{column}__failed"))
            .sum()
            .alias(column)
            for column in ORDER_TIMESTAMPS
        )
        .row(0)
    )
    unparsed = {
        column: total
        for column, total in zip(ORDER_TIMESTAMPS, counts, strict=True)
        if total
    }
    if unparsed:
        detail = "; ".join(
            f"{column}: {total} valores"
            for column, total in sorted(unparsed.items())
        )
        raise ContractViolation(
            "silver.orders recibió texto no interpretable como fecha "
            f"({detail}). Una falla de formato no puede convertirse en nulo."
        )


def build_orders(orders: pl.DataFrame) -> pl.DataFrame:
    """Tipa fechas de órdenes y comprueba su secuencia temporal."""
    _require_columns(
        orders,
        "silver.orders",
        ("order_id", "customer_id", "order_status", *ORDER_TIMESTAMPS),
    )

    typed = orders.with_columns(
        _parse_timestamp(orders.schema[column], column)
        for column in ORDER_TIMESTAMPS
    )
    _reject_unparsed_timestamps(orders, typed)

    statuses = set(typed["order_status"].drop_nulls().unique().to_list())
    unknown = statuses - ALLOWED_ORDER_STATUSES
    if typed["order_status"].null_count() > 0:
        raise ContractViolation("silver.orders no admite estados nulos.")
    if unknown:
        raise ContractViolation(
            "silver.orders recibió estados fuera del contrato: "
            f"{', '.join(sorted(unknown))}."
        )

    result = typed.with_columns(
        (
            (pl.col("order_status") == "delivered")
            & pl.col("order_delivered_customer_date").is_null()
        ).alias("delivery_timestamp_missing")
    )

    out_of_sequence = result.filter(
        (pl.col("order_status") == "delivered")
        & (
            pl.col("order_delivered_customer_date")
            < pl.col("order_purchase_timestamp")
        )
    ).height
    if out_of_sequence:
        raise ContractViolation(
            f"silver.orders tiene {out_of_sequence} órdenes entregadas antes "
            "de su fecha de compra."
        )
    return result


def build_customers(customers: pl.DataFrame) -> pl.DataFrame:
    """Conserva clientes y verifica la relación uno a uno con customer_id."""
    _require_columns(customers, "silver.customers", CUSTOMER_COLUMNS)
    result = customers.select(CUSTOMER_COLUMNS)

    nulls = result.select(
        pl.any_horizontal(
            pl.col(column).is_null() for column in CUSTOMER_COLUMNS
        )
        .sum()
        .alias("nulos")
    ).item()
    if nulls:
        raise ContractViolation(
            f"silver.customers tiene {nulls} filas con identidad nula."
        )
    if result["customer_id"].n_unique() != result.height:
        raise ContractViolation(
            "silver.customers no respeta una fila por customer_id."
        )
    return result


def _reject_invalid_amounts(
    frame: pl.DataFrame, table: str, columns: tuple[str, ...]
) -> None:
    """Rechaza montos no finitos o negativos sin imputarlos ni borrarlos."""
    non_finite = frame.select(
        (pl.col(column).is_not_null() & ~pl.col(column).is_finite())
        .sum()
        .alias(column)
        for column in columns
    ).row(0)
    offenders = {
        column: total
        for column, total in zip(columns, non_finite, strict=True)
        if total
    }
    if offenders:
        detail = "; ".join(
            f"{column}: {total} filas"
            for column, total in sorted(offenders.items())
        )
        raise ContractViolation(
            f"{table} recibió montos no finitos ({detail})."
        )

    negatives = frame.select(
        (pl.col(column) < 0).sum().alias(column) for column in columns
    ).row(0)
    offenders = {
        column: total
        for column, total in zip(columns, negatives, strict=True)
        if total
    }
    if offenders:
        detail = "; ".join(
            f"{column}: {total} filas"
            for column, total in sorted(offenders.items())
        )
        raise ContractViolation(f"{table} recibió montos negativos ({detail}).")


def build_order_items(items: pl.DataFrame) -> pl.DataFrame:
    """Comprueba que los ítems no tengan precios ni fletes negativos."""
    _require_columns(
        items,
        "silver.order_items",
        ("order_id", "order_item_id", *ITEM_AMOUNTS),
    )
    _reject_invalid_amounts(items, "silver.order_items", ITEM_AMOUNTS)
    return items


def build_payments(payments: pl.DataFrame) -> pl.DataFrame:
    """Comprueba que los pagos no tengan montos negativos."""
    _require_columns(
        payments,
        "silver.payments",
        ("order_id", "payment_sequential", *PAYMENT_AMOUNTS),
    )
    _reject_invalid_amounts(payments, "silver.payments", PAYMENT_AMOUNTS)
    return payments


def validate_relationships(
    orders: pl.DataFrame,
    customers: pl.DataFrame,
    items: pl.DataFrame,
    payments: pl.DataFrame,
) -> None:
    """Verifica las claves foráneas antes de construir productos Gold."""
    relationships = (
        ("silver.orders.customer_id", "customer_id", orders, customers),
        ("silver.order_items.order_id", "order_id", items, orders),
        ("silver.payments.order_id", "order_id", payments, orders),
    )
    orphans = {
        label: left.join(right.select(key).unique(), on=key, how="anti").height
        for label, key, left, right in relationships
    }
    failed = {label: total for label, total in orphans.items() if total}
    if failed:
        detail = "; ".join(
            f"{label}: {total} filas" for label, total in sorted(failed.items())
        )
        raise ContractViolation(
            f"Silver detectó una clave foránea huérfana ({detail}). "
            "No se publica la capa."
        )
