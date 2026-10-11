"""Extracción de embeddings de imágenes con un extractor preentrenado."""

from collections.abc import Callable
from itertools import pairwise
from pathlib import Path

import numpy as np
import torch
from PIL import Image


def dividir_en_tiles(imagen: Image.Image, n: int) -> list[Image.Image]:
    """Divide `imagen` en `n` tiles verticales, sin solape y sin perder nada.

    Cada tile tiene el alto completo de `imagen` y un ancho de
    `imagen.width // n`; el último tile se extiende hasta el borde derecho
    para cubrir el resto que deja la división entera. Juntos, los tiles
    cubren exactamente el cuadrante original.
    """
    if n < 1:
        raise ValueError(f"n debe ser al menos 1; recibió {n}.")
    ancho_tile = imagen.width // n
    if ancho_tile == 0:
        raise ValueError(
            f"No se puede dividir un ancho de {imagen.width} px en {n} tiles."
        )
    bordes = [i * ancho_tile for i in range(n)] + [imagen.width]
    return [
        imagen.crop((izquierda, 0, derecha, imagen.height))
        for izquierda, derecha in pairwise(bordes)
    ]


def extraer_embeddings(
    rutas: list[Path],
    modelo: Callable[[torch.Tensor], torch.Tensor],
    transformacion: Callable[[Image.Image], torch.Tensor],
    tamano_lote: int = 16,
) -> np.ndarray:
    """Extrae un embedding por imagen, en el mismo orden que `rutas`.

    `modelo` es cualquier invocable que recibe un tensor `(lote, canales,
    alto, ancho)` y devuelve `(lote, dimensión)` — en la pauta es un
    extractor de `timm` en modo evaluación (`model.eval()`), y en las
    pruebas puede ser un doble liviano. Cada imagen se abre, se le aplica
    `transformacion` (el preprocesamiento que declara el propio modelo) y
    se agrupa en lotes de `tamano_lote` antes de pasar por `modelo`, sin
    calcular gradientes. El resultado es un arreglo `(len(rutas),
    dimensión)`.
    """
    if tamano_lote < 1:
        raise ValueError(
            f"tamano_lote debe ser al menos 1; recibió {tamano_lote}."
        )
    lotes = []
    with torch.no_grad():
        for inicio in range(0, len(rutas), tamano_lote):
            tensores = []
            for ruta in rutas[inicio : inicio + tamano_lote]:
                with Image.open(ruta) as imagen:
                    tensores.append(transformacion(imagen.convert("RGB")))
            salida = modelo(torch.stack(tensores))
            lotes.append(salida.detach().cpu().numpy())
    return np.concatenate(lotes, axis=0)
