from .sensores import Sensor


def contar_riesgos(
    sensores: list[Sensor],
    lecturas: dict[str, list[float]],
) -> dict[str, int]:
    conteo = {}

    for sensor in sensores:
        conteo[sensor.nombre] = 0

        for valor in lecturas.get(sensor.nombre, []):
            if sensor.es_riesgo(valor):
                conteo[sensor.nombre] += 1

    return conteo
