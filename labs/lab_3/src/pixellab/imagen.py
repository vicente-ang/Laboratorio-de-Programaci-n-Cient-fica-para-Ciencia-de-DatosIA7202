"""Clase ``Imagen``: contenedor de imágenes sobre el que se opera con NumPy."""

from __future__ import annotations

import numpy as np


class Imagen:
    """Contenedor de imágenes RGB.

    Completen el constructor y los operadores de esta clase siguiendo el
    contrato del enunciado y los tests de ``tests/test_imagen.py``.
    """

    def __init__(self, img: np.ndarray) -> None:
        if not isinstance(img, np.ndarray):
            raise TypeError(
                "Debes entregar un arreglo de numpy como argumento del constructor de Imagen"
            )

        if img.ndim != 3:
            raise ValueError("La imagen debe tener 3 dimensiones")

        if img.shape[-1] != 3:
            raise ValueError("La imagen debe tener 3 canales")

        self.imagen = img

    def __add__(self, other):
        # acá se checkea si es imágen, y si es así other se convierte en el arreglo
        if isinstance(other, Imagen):
            other = other.imagen
        # acá se valida que coincidan las dimensiones con la imágen original
        if isinstance(other, np.ndarray):
            if self.imagen.shape != other.shape:
                raise ValueError(
                    "Las dimensiones de la imagen a operar (alto x ancho x canales) no calzan con las de la imagen original (alto xancho x canales)"
                )
        # si no es ni int, float, imagen ni arreglo, se considera dato no válido
        elif not isinstance(other, (int, float)):
            raise TypeError("Tipo de dato no válido")

        resultado = (self.imagen + other).astype(int)
        # Se satura según el rango
        resultado[resultado > 255] = 255
        resultado[resultado < 0] = 0
        # se entrega la co´pia de la imágen
        return Imagen(np.copy(resultado))

    def __radd__(self, other: int | float | np.ndarray | Imagen) -> Imagen:
        # suma es conmutativa
        return self.__add__(other)

    def __sub__(self, other: int | float | np.ndarray | Imagen) -> Imagen:
        # acá se checkea si es imágen, y si es así other se convierte en el arreglo
        if isinstance(other, Imagen):
            other = other.imagen
        # acá se valida que coincidan las dimensiones con la imágen original
        if isinstance(other, np.ndarray):
            if self.imagen.shape != other.shape:
                raise ValueError(
                    "Las dimensiones de la imagen a operar (alto x ancho x canales) no calzan con las de la imagen original (alto xancho x canales)"
                )
        # si no es ni int, float, imagen ni arreglo, se considera dato no válido
        elif not isinstance(other, (int, float)):
            raise TypeError("Tipo de dato no válido")

        resultado = (self.imagen - other).astype(int)
        # Se satura según el rango
        resultado[resultado > 255] = 255
        resultado[resultado < 0] = 0
        # se entrega la co´pia de la imágen
        return Imagen(np.copy(resultado))

    def __rsub__(self, other: int | float | np.ndarray | Imagen) -> Imagen:
        # acá se checkea si es imágen, y si es así other se convierte en el arreglo
        if isinstance(other, Imagen):
            other = other.imagen
        # acá se valida que coincidan las dimensiones con la imágen original
        if isinstance(other, np.ndarray):
            if self.imagen.shape != other.shape:
                raise ValueError(
                    "Las dimensiones de la imagen a operar (alto x ancho x canales) no calzan con las de la imagen original (alto xancho x canales)"
                )
        # si no es ni int, float, imagen ni arreglo, se considera dato no válido
        elif not isinstance(other, (int, float)):
            raise TypeError("Tipo de dato no válido")

        resultado = (other - self.imagen).astype(int)
        # Se satura según el rango
        resultado[resultado > 255] = 255
        resultado[resultado < 0] = 0
        # se entrega la co´pia de la imágen
        return Imagen(np.copy(resultado))

    def __mul__(self, other: int | float | np.ndarray | Imagen) -> Imagen:
        # acá se checkea si es imágen, y si es así other se convierte en el arreglo
        if isinstance(other, Imagen):
            other = other.imagen
        # acá se valida que coincidan las dimensiones con la imágen original
        if isinstance(other, np.ndarray):
            if self.imagen.shape != other.shape:
                raise ValueError(
                    "Las dimensiones de la imagen a operar (alto x ancho x canales) no calzan con las de la imagen original (alto xancho x canales)"
                )
        # si no es ni int, float, imagen ni arreglo, se considera dato no válido
        elif not isinstance(other, (int, float)):
            raise TypeError("Tipo de dato no válido")

        resultado = (self.imagen * other).astype(int)
        # Se satura según el rango
        resultado[resultado > 255] = 255
        resultado[resultado < 0] = 0
        # se entrega la co´pia de la imágen
        return Imagen(np.copy(resultado))

    def __rmul__(self, other: int | float | np.ndarray | Imagen) -> Imagen:
        # multiplicación es conmutativa
        return self.__mul__(other)
