"""Productos analíticos Gold de Pudubella."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import polars as pl

from src.pudulake.contracts import ContractViolation

DELIVERED = "delivered"
EXCLUSION_REASON = "delivered_order_without_payment"
DEFAULT_SEGMENT = "Others"

RULE_EXPRESSIONS = {
    "max_recency_days": lambda value: pl.col("recency_days") <= value,
    "min_recency_days": lambda value: pl.col("recency_days") >= value,
    "min_frequency": lambda value: pl.col("frequency") >= value,
    "max_frequency": lambda value: pl.col("frequency") <= value,
    "min_monetary": lambda value: pl.col("monetary") >= value,
    "max_monetary": lambda value: pl.col("monetary") <= value,
}


def _delivered(orders: pl.DataFrame) -> pl.DataFrame:
    """Filtra las órdenes efectivamente entregadas."""
    return orders.filter(pl.col("order_status") == DELIVERED)


def _paid_orders(payments: pl.DataFrame) -> pl.DataFrame:
    """Agrega los pagos al grano de orden antes de cualquier unión."""
    return payments.group_by("order_id").agg(
        pl.col("payment_value").sum().alias("order_payment_value")
    )


def build_rfm_exclusions(
    orders: pl.DataFrame, payments: pl.DataFrame
) -> pl.DataFrame:
    """Registra órdenes entregadas sin pago para excluirlas de RFM."""
    return (
        _delivered(orders)
        .join(payments.select("order_id").unique(), on="order_id", how="anti")
        .select("order_id", "customer_id", "order_purchase_timestamp")
        .with_columns(pl.lit(EXCLUSION_REASON).alias("reason"))
        .sort("order_id")
    )


def build_sales_daily(
    orders: pl.DataFrame, items: pl.DataFrame
) -> pl.DataFrame:
    """Construye ventas de ítems por fecha de compra y órdenes entregadas."""
    delivered = _delivered(orders).select(
        "order_id",
        pl.col("order_purchase_timestamp").dt.date().alias("sale_date"),
    )
    return (
        delivered.join(
            items.select("order_id", "price"), on="order_id", how="inner"
        )
        .group_by("sale_date")
        .agg(
            pl.col("price").sum().alias("items_sold_value"),
            pl.col("order_id")
            .n_unique()
            .cast(pl.Int64)
            .alias("delivered_orders"),
        )
        .sort("sale_date")
    )


def _segment_expression(segments: dict[str, Any]) -> pl.Expr:
    """Traduce las reglas congeladas del YAML a una única expresión."""
    unknown = {
        rule
        for rules in segments.values()
        for rule in rules
        if rule not in RULE_EXPRESSIONS
    }
    if unknown:
        raise ContractViolation(
            "gold.customer_rfm recibió reglas de segmento desconocidas: "
            f"{', '.join(sorted(unknown))}."
        )
    expression = pl.lit(DEFAULT_SEGMENT)
    for name, rules in reversed(list(segments.items())):
        condition = pl.lit(True)
        for rule, value in rules.items():
            condition = condition & RULE_EXPRESSIONS[rule](value)
        label = name.replace("_", " ").title()
        expression = (
            pl.when(condition).then(pl.lit(label)).otherwise(expression)
        )
    return expression.alias("segment")


def build_customer_rfm(
    orders: pl.DataFrame,
    customers: pl.DataFrame,
    payments: pl.DataFrame,
    segments: dict[str, Any],
) -> pl.DataFrame:
    """Calcula RFM de compras entregadas y aplica reglas congeladas."""
    rules = segments.get("segments", segments)
    if not isinstance(rules, dict) or not rules:
        raise ContractViolation(
            "gold.customer_rfm necesita segmentos declarados en "
            "config/rfm_segments.yaml."
        )

    eligible = (
        _delivered(orders)
        .join(_paid_orders(payments), on="order_id", how="inner")
        .join(
            customers.select("customer_id", "customer_unique_id"),
            on="customer_id",
            how="inner",
        )
    )
    if eligible.is_empty():
        raise ContractViolation(
            "gold.customer_rfm no encontró órdenes entregadas con pago."
        )

    reference_date = eligible["order_purchase_timestamp"].dt.date().max() + (
        timedelta(days=1)
    )

    return (
        eligible.group_by("customer_unique_id")
        .agg(
            pl.col("order_purchase_timestamp").max().alias("last_purchase"),
            pl.col("order_id").n_unique().cast(pl.Int64).alias("frequency"),
            pl.col("order_payment_value").sum().alias("monetary"),
        )
        .with_columns(
            pl.lit(reference_date, dtype=pl.Date).alias("reference_date"),
            (
                pl.lit(reference_date, dtype=pl.Date)
                - pl.col("last_purchase").dt.date()
            )
            .dt.total_days()
            .cast(pl.Int64)
            .alias("recency_days"),
        )
        .with_columns(_segment_expression(rules))
        .select(
            "customer_unique_id",
            "last_purchase",
            "recency_days",
            "frequency",
            "monetary",
            "reference_date",
            "segment",
        )
        .sort("customer_unique_id")
    )
