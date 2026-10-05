"""Búsqueda de vecinos más cercanos sobre una representación."""

import numpy as np
import polars as pl
from sklearn.neighbors import NearestNeighbors


def vecinos_mas_cercanos(
    X: np.ndarray,
    nombres: list[str],
    consulta: str,
    k: int = 5,
    metrica: str = "euclidean",
) -> pl.DataFrame:
    """Devuelve los `k` personajes más cercanos a `consulta`.

    `X` tiene una fila por personaje, en el mismo orden que `nombres`; puede
    ser un arreglo de NumPy o una matriz dispersa, como la de TF-IDF. El
    resultado tiene las columnas `name` y `distancia`, ordenadas de menor a
    mayor distancia, y no incluye a la consulta. Si `consulta` no está en
    `nombres`, levanta `KeyError`.
    """
    if consulta not in nombres:
        raise KeyError(f"La consulta {consulta!r} no está en nombres.")

    indice_consulta = nombres.index(consulta)
    n_vecinos = min(k + 1, len(nombres))

    modelo = NearestNeighbors(n_neighbors=n_vecinos, metric=metrica).fit(X)
    distancias, indices = modelo.kneighbors(X[indice_consulta : indice_consulta + 1])

    indices = indices[0]
    distancias = distancias[0]

    # Quitamos explícitamente el índice de la consulta. Esto es más robusto
    # que asumir que siempre será el primer elemento cuando existen empates.
    mascara = indices != indice_consulta
    indices = indices[mascara][:k]
    distancias = distancias[mascara][:k]

    nombres_array = np.asarray(nombres, dtype=object)
    return pl.DataFrame(
        {
            "name": nombres_array[indices].tolist(),
            "distancia": distancias.astype(float).tolist(),
        }
    )
