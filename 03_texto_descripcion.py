import random

import pandas as pd

ACCIONES = {
    "Robo": ["me arrebató la mochila", "me quitó el celular a la fuerza", "sustrajo mis pertenencias"],
    "Robo agravado": ["me amenazó con un arma y me robó", "un grupo armado asaltó el local", "me golpeó y robó mis pertenencias"],
    "Hurto": ["se llevó mi bicicleta sin que me diera cuenta", "sustrajo mi mochila del asiento"],
    "Estafa": ["me ofreció un producto falso y me cobró de más", "me hizo transferir dinero con engaños"],
    "Homicidio": ["atacó con arma de fuego a otra persona dejándola sin signos vitales", "provocó, con un arma blanca, la muerte de otra persona"],
    "Lesiones": ["golpeó fuertemente a otra persona en la vía pública", "agredió físicamente a un vecino"],
    "Terrorismo": ["dejó un paquete sospechoso cerca de una entidad pública", "amenazó con un artefacto explosivo"],
    "Tenencia ilegal de armas": ["portaba un arma de fuego sin permiso a la vista de todos", "mostró un arma de forma amenazante"],
    "Tráfico de drogas": ["vendía sustancias ilícitas en la esquina", "distribuía paquetes sospechosos a menores"],
    "Secuestro": ["subió a una persona a la fuerza a un vehículo", "retuvo contra su voluntad a un menor"],
    "Violación": ["agredió sexualmente a otra persona"],
    "Amenazas": ["amenazó de muerte a un vecino", "envió mensajes amenazantes reiterados"],
    "Otros": ["realizó una actividad sospechosa no identificada claramente"],
}

MOMENTOS_DIA = {
    (0, 6): "de madrugada",
    (6, 12): "en la mañana",
    (12, 18): "en la tarde",
    (18, 24): "en la noche",
}

LUGARES = [
    "en la vía pública", "cerca de un paradero de transporte público",
    "en un parque del distrito", "frente a un centro comercial",
    "en una calle residencial", "cerca de un mercado local",
]


def _momento_dia(hora: int) -> str:
    for (ini, fin), etiqueta in MOMENTOS_DIA.items():
        if ini <= hora < fin:
            return etiqueta
    return "en horario no determinado"


def generar_descripcion(clasificacion_delito: str, fecha_hora, seed: int | None = None) -> str:
    rng = random.Random(seed)
    accion = rng.choice(ACCIONES.get(clasificacion_delito, ACCIONES["Otros"]))
    lugar = rng.choice(LUGARES)
    momento = _momento_dia(
        fecha_hora.hour if hasattr(fecha_hora, "hour") else 12)
    plantilla = rng.choice([
        "Presencié cómo una persona {accion} {lugar}, {momento}.",
        "Un sujeto {accion} {lugar}, {momento}. Solicito verificación urgente.",
        "Se reporta que un individuo {accion} {lugar}, {momento}.",
    ])
    return plantilla.format(accion=accion, lugar=lugar, momento=momento)


def generar_descripciones(df: pd.DataFrame, seed: int = 42) -> pd.Series:
    rng = random.Random(seed)
    return df.apply(
        lambda row: generar_descripcion(
            row["clasificacion_delito"], row["fecha_hora"], seed=rng.randint(
                0, 10**6)
        ),
        axis=1,
    )


if __name__ == "__main__":
    import datetime as dt

    ejemplos = [
        ("Robo agravado", dt.datetime(2025, 3, 1, 22, 10)),
        ("Homicidio", dt.datetime(2025, 6, 15, 2, 30)),
        ("Estafa", dt.datetime(2025, 8, 20, 15, 0)),
    ]
    for clasificacion, fecha in ejemplos:
        print(f"[{clasificacion}] -> {generar_descripcion(clasificacion, fecha)}")
