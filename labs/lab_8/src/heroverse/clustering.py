"""Evaluación de agrupamientos y búsqueda de equivalentes."""

from itertools import combinations

import numpy as np
import polars as pl
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.metrics.pairwise import pairwise_distances


def elegir_k(X: np.ndarray, ks: list[int], semilla: int = 0) -> pl.DataFrame:
    """Reporta inercia y silhouette para los valores de k indicados."""
    if any(k < 2 or k >= len(X) for k in ks):
        raise ValueError("Cada k debe estar entre 2 y n-1.")
    filas = []
    for k in ks:
        modelo = KMeans(n_clusters=k, n_init=10, random_state=semilla)
        etiquetas = modelo.fit_predict(X)
        valor = silhouette_score(X, etiquetas)
        filas.append({"k": k, "inercia": float(modelo.inertia_), "silhouette": float(valor)})
    return pl.DataFrame(filas, schema={"k": pl.Int64, "inercia": pl.Float64, "silhouette": pl.Float64})


def estabilidad(X: np.ndarray, k: int, semillas: list[int]) -> float:
    """Promedia el ARI de todos los pares de semillas independientes."""
    if len(semillas) < 2:
        raise ValueError("Se necesitan al menos dos semillas.")
    etiquetas = [
        KMeans(n_clusters=k, n_init=1, random_state=s).fit_predict(X)
        for s in semillas
    ]
    return float(np.mean([
        adjusted_rand_score(a, b) for a, b in combinations(etiquetas, 2)
    ]))


def perfil_clusters(
    features: pl.DataFrame, etiquetas: np.ndarray, columnas: list[str]
) -> pl.DataFrame:
    """Devuelve el tamaño y las medias de cada grupo."""
    if features.height != len(etiquetas):
        raise ValueError("Las etiquetas deben corresponder a cada fila.")
    return (
        features.with_columns(pl.Series("cluster", etiquetas))
        .group_by("cluster")
        .agg(pl.len().alias("n"), *[pl.col(c).mean() for c in columnas])
        .sort("cluster")
        .select("cluster", "n", *columnas)
    )


def equivalentes(
    X: np.ndarray,
    personajes: pl.DataFrame,
    consulta: str,
    k: int = 5,
    excluir_creator: str = "Marvel Comics",
    metrica: str = "cosine",
) -> pl.DataFrame:
    """Busca fuera de una editorial, conservando creadores desconocidos."""
    nombres = personajes["name"].to_list()
    if consulta not in nombres:
        raise KeyError(consulta)
    if len(nombres) != X.shape[0]:
        raise ValueError("Los nombres y las filas de X no coinciden.")
    origen = nombres.index(consulta)
    creadores = personajes["creator"].to_list()
    candidatos = [
        i for i, creador in enumerate(creadores)
        if i != origen and creador != excluir_creator
    ]
    if not candidatos or k <= 0:
        return pl.DataFrame(schema={"name": pl.String, "creator": pl.String, "distancia": pl.Float64})
    distancias = pairwise_distances(X[candidatos], X[origen : origen + 1], metric=metrica).ravel()
    elegidos = np.argsort(distancias, kind="stable")[:k]
    return pl.DataFrame({
        "name": [nombres[candidatos[j]] for j in elegidos],
        "creator": [creadores[candidatos[j]] for j in elegidos],
        "distancia": distancias[elegidos].astype(float).tolist(),
    })
