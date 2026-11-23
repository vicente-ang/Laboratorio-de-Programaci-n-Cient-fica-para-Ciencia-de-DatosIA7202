"""Rutas de inferencia: información del modelo, vida y predicción."""

from typing import Any

from fastapi import APIRouter, Depends

from src.aguaapr.artifacts import a_tabla, predecir
from src.aguaapr.constants import FEATURES, OPCIONALES, RANGOS
from src.aguaapr.contracts import RespuestaPrediccion, Servicios
from src.aguaapr.deps import crear_dependencia_clave
from src.aguaapr.validation import MedicionAgua


def crear_router_inferencia(servicios: Servicios) -> APIRouter:
    """Construye el router con tres rutas.

    - `GET /`: describe el modelo. Responde las métricas de validación de la
      metadata, la entrada (cada columna con su rango) y la
      salida.
    - `GET /health`: ruta de vida, pública. Responde
      `{"estado": "ok"}`.
    - `POST /predict`: recibe una `MedicionAgua` en el cuerpo y responde una
      `RespuestaPrediccion` con la predicción y su probabilidad. Exige la
      clave de API con `crear_dependencia_clave`.
    """
    router = APIRouter()
    exigir_clave = crear_dependencia_clave(servicios)

    @router.get("/")
    def informacion() -> dict[str, Any]:
        entrada = {
            nombre: {
                "minimo": RANGOS[nombre][0],
                "maximo": RANGOS[nombre][1],
                "puede_faltar": nombre in OPCIONALES,
            }
            for nombre in FEATURES
        }
        return {
            "metricas_validacion": servicios.metadata["metricas_validacion"],
            "entrada": entrada,
            "salida": {
                "prediccion": "1 si el modelo estima que el agua es potable, "
                "0 si no lo es",
                "probabilidad": "probabilidad estimada de que el agua sea "
                "potable, entre 0 y 1",
            },
        }

    @router.get("/health")
    def vida() -> dict[str, str]:
        return {"estado": "ok"}

    @router.post(
        "/predict",
        response_model=RespuestaPrediccion,
        dependencies=[Depends(exigir_clave)],
    )
    def predict(medicion: MedicionAgua) -> RespuestaPrediccion:
        clases, probabilidades = predecir(servicios.modelo, a_tabla([medicion]))
        return RespuestaPrediccion(
            prediccion=int(clases[0]),
            probabilidad=round(float(probabilidades[0]), 4),
        )

    return router
