"""Métricas de regresión para la biomasa de pradera."""

import numpy as np
from sklearn.metrics import r2_score

from src.pasturecam.contratos import AREA_CUADRANTE_M2, PESOS_OBJETIVOS

M2_POR_HECTAREA = 10_000
GRAMOS_POR_KG = 1_000


def r2_log_ponderado(
    y_real: dict[str, np.ndarray],
    y_pred: dict[str, np.ndarray],
    pesos: dict[str, float] = PESOS_OBJETIVOS,
) -> float:
    """R² sobre `log1p` de cada objetivo, combinado con `pesos`.

    `y_real` y `y_pred` son diccionarios `{nombre_objetivo: valores}`, con
    las mismas claves que `pesos` (por omisión, las cinco de
    `PESOS_OBJETIVOS`). Cada valor se recorta a 0 antes de aplicar
    `log1p`, porque una predicción negativa de biomasa no tiene sentido
    físico y `log1p` de un número menor que -1 no está definido. El
    resultado es la suma ponderada de los R² por objetivo; vale 1,0 si las
    predicciones son idénticas a los valores reales.
    """
    faltantes = set(pesos) - (set(y_real) & set(y_pred))
    if faltantes:
        raise KeyError(
            f"Faltan objetivos en y_real o y_pred: {sorted(faltantes)}."
        )
    total = 0.0
    for nombre, peso in pesos.items():
        reales = np.log1p(np.clip(np.asarray(y_real[nombre]), 0, None))
        predichos = np.log1p(np.clip(np.asarray(y_pred[nombre]), 0, None))
        # r2_score no está definido si los reales son constantes y deja
        # 0,0; si además coinciden con lo predicho, el ajuste es perfecto.
        if np.allclose(reales, predichos):
            total += peso
        else:
            total += peso * r2_score(reales, predichos)
    return float(total)


def gramos_a_kg_ha(gramos: float) -> float:
    """Convierte gramos por cuadrante de 70 x 30 cm a kilogramos por hectárea.

    Un cuadrante mide `AREA_CUADRANTE_M2` m². Una hectárea tiene 10 000 m².
    `gramos_a_kg_ha(1)` da aproximadamente 47,6: un gramo en el cuadrante
    equivale a esa cantidad de kilogramos repartidos en una hectárea.
    """
    return gramos / AREA_CUADRANTE_M2 * M2_POR_HECTAREA / GRAMOS_POR_KG
