import argparse
from pathlib import Path

from src.agroalerta.datos import cargar_lecturas
from src.agroalerta.reporte import contar_riesgos
from src.agroalerta.sensores import (
    SensorHumedad,
    SensorTemperatura,
    SensorViento,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="AgroAlerta")
    parser.add_argument("--fecha", default="2026-06-15")
    args = parser.parse_args()

    sensores = [
        SensorTemperatura(0, 40),
        SensorViento(25),
        SensorHumedad(85),
    ]

    ruta = Path(__file__).parent / "data" / "lecturas.csv"

    lecturas = cargar_lecturas(ruta, args.fecha)
    conteo = contar_riesgos(sensores, lecturas)

    print(f"Estación Parcela Norte — {args.fecha}")
    print(f"Temperatura    {conteo['temperatura']} lecturas en riesgo")
    print(f"Viento         {conteo['viento']} lecturas en riesgo")
    print(f"Humedad        {conteo['humedad']} lecturas en riesgo")

    print()
    print(f"Total: {sum(conteo.values())} situaciones de riesgo")


if __name__ == "__main__":
    main()
