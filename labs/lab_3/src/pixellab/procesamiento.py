"""Operaciones de procesamiento de imágenes para completar."""

from __future__ import annotations

import numpy as np
from scipy.signal import convolve2d

from src.pixellab.imagen import Imagen


class LibImagen:
    """Filtros y transformaciones que reciben y retornan ``Imagen``."""

    def to_negative(self, img_in: Imagen) -> Imagen:
        resultado = (255 - img_in.imagen).astype(int)
        return Imagen(np.copy(resultado))

    def to_gray(self, img_in: Imagen) -> Imagen:
        R = img_in.imagen[:, :, 0]
        G = img_in.imagen[:, :, 1]
        B = img_in.imagen[:, :, 2]
        # Formula
        gris = 0.299 * R + 0.587 * G + 0.114 * B

        gris_rgb = np.stack([gris, gris, gris], axis=2)

        return Imagen(np.copy(gris_rgb.astype(int)))

    def get_channel(self, img_in: Imagen, channel: str) -> Imagen:

        canales = {"r": 0, "g": 1, "b": 2}

        if channel not in canales:
            raise ValueError(
                "Canal 'x' no válido. Valores posibles: 'r', 'g' o 'b'."
            )

        resultado = np.zeros_like(img_in.imagen)

        indice = canales[channel]

        resultado[:, :, indice] = img_in.imagen[:, :, indice]

        return Imagen(np.copy(resultado))

    def flip(self, img_in: Imagen, axis: str) -> Imagen:
        ejes = {"v": 0, "h": 1}

        if axis not in ejes:
            raise ValueError(
                "Eje 'x' no válido. Valores posibles: 'h' (horizontal) o 'v' (vertical)."
            )
        indice = ejes[axis]

        resultado = np.flip(img_in.imagen, axis=indice).astype(int)

        resultado[resultado > 255] = 255
        resultado[resultado < 0] = 0

        return Imagen(np.copy(resultado))

    def set_saturation(self, img_in: Imagen, C: float) -> Imagen:

        gris = self.to_gray(img_in).imagen

        R = gris + C * (img_in.imagen - gris)

        R = R.astype(int)

        R[R > 255] = 255
        R[R < 0] = 0

        return Imagen(np.copy(R))

    def set_contrast(self, img_in: Imagen, C: float) -> Imagen:

        F = 259 * (C + 255) / (255 * (259 - C))

        R = F * (img_in.imagen - 128) + 128

        R = R.astype(int)

        R[R > 255] = 255
        R[R < 0] = 0

        return Imagen(np.copy(R))

    def conv_channel(self, img_in: Imagen, kernel: np.ndarray) -> Imagen:
        """Aplica un filtro sobre cada uno de los canales RGB por separado usando un kernel, y luego los vuelve
        a juntar con np.stack. El kernel define cómo se combinan los valores de cada píxel con sus vecinos,
        para producir un efecto, como lo puede ser enfoque, desenfoque, etc.
        Además, se asegura que la imágen resultante se mantenga del tamaño de la imágen original con same."""
        # El cuerpo de este método lo entrega el curso.
        img = img_in.imagen
        img_out = []
        for i in range(img.shape[-1]):
            img_channel = convolve2d(
                img[:, :, i], kernel, mode="same", boundary="symm"
            )
            img_out.append(img_channel)
        new_image = np.stack(img_out, axis=2)
        new_image[new_image > 255], new_image[new_image < 0] = 255, 0
        return Imagen(new_image.astype(int))
