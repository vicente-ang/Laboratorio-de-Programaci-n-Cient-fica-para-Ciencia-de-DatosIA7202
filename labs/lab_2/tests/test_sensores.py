from src.agroalerta.reporte import contar_riesgos
from src.agroalerta.sensores import (
    SensorHumedad,
    SensorTemperatura,
    SensorViento,
)


def test_temperatura_bajo_cero_es_riesgosa() -> None:
    sensor = SensorTemperatura(0, 40)

    assert sensor.es_riesgo(-2) is True


def test_temperatura_templada_no_es_riesgosa() -> None:
    sensor = SensorTemperatura(0, 40)

    assert sensor.es_riesgo(18) is False


def test_viento_normal_no_es_riesgoso() -> None:
    sensor = SensorViento(25)

    assert sensor.es_riesgo(10) is False


def test_contar_riesgos() -> None:
    sensores = [
        SensorTemperatura(0, 40),
        SensorViento(25),
        SensorHumedad(85),
    ]

    lecturas = {
        "temperatura": [18, -2, 42],
        "viento": [10, 30],
        "humedad": [70, 90],
    }

    conteo = contar_riesgos(sensores, lecturas)

    assert conteo == {
        "temperatura": 2,
        "viento": 1,
        "humedad": 1,
    }
