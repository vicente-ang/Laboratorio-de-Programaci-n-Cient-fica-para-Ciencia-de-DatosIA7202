"""Kernels de convolución que deben definir para la Etapa 6."""

import numpy as np

# Su código aquí: agreguen al menos cinco tuplas (nombre, kernel).
KERNELS: list[tuple[str, np.ndarray]] = [
    # El kernel identidad mantiene la imagen original porque solo considera
    # el píxel central y no modifica la influencia de los vecinos.
    ("identidad", np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]])),
    # El kernel laplaciano detecta bordes al resaltar diferencias de
    # intensidad entre un píxel y sus vecinos.
    ("laplaciano", np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])),
    # El kernel de enfoque aumenta la nitidez destacando el píxel central
    # y reduciendo la influencia de los píxeles vecinos.
    ("enfoque", np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])),
    # El kernel de desenfoque calcula un promedio entre los píxeles vecinos,
    # generando una imagen más suave y menos detallada.
    (
        "desenfoque",
        np.array(
            [
                [1 / 9, 1 / 9, 1 / 9],
                [1 / 9, 1 / 9, 1 / 9],
                [1 / 9, 1 / 9, 1 / 9],
            ]
        ),
    ),
    # El kernel de relieve genera diferencias en distintas direcciones
    # que producen un efecto visual similar a sombras y profundidad.
    ("relieve", np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]])),
]
