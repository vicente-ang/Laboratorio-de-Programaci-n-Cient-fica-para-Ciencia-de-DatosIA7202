class Sensor:
    def __init__(self, nombre: str, unidad: str) -> None:
        self.nombre = nombre
        self.unidad = unidad

    def es_riesgo(self, valor: float) -> bool:
        return False