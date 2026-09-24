import json
import random
from pathlib import Path

import pandas as pd
from shapely.geometry import shape, Point

GEOJSON_PATH = Path(__file__).parent / "peru_distrital_simple.geojson"
GEOJSON_URL = "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_distrital_simple.geojson"


def cargar_distritos(path: Path = GEOJSON_PATH) -> list[dict]:
    """Carga el GeoJSON real y devuelve una lista de dicts con geometría + metadatos."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    distritos = []
    for feat in data["features"]:
        props = feat["properties"]
        if feat.get("geometry") is None:
            continue
        geom = shape(feat["geometry"])
        if geom.is_empty:
            continue
        distritos.append(
            {
                "departamento": props["NOMBDEP"],
                "provincia": props["NOMBPROV"],
                "distrito": props["NOMBDIST"],
                "iddist": props["IDDIST"],
                "geometry": geom,
            }
        )
    return distritos


def punto_aleatorio_en_poligono(geom, max_intentos: int = 200) -> Point:
    minx, miny, maxx, maxy = geom.bounds
    for _ in range(max_intentos):
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if geom.contains(p):
            return p

    return geom.representative_point()


def generar_ubicaciones(n: int, distritos: list[dict], pesos_departamento: dict | None = None,
                        seed: int = 42) -> pd.DataFrame:

    random.seed(seed)

    por_departamento: dict[str, list[dict]] = {}
    for d in distritos:
        por_departamento.setdefault(d["departamento"], []).append(d)

    if pesos_departamento:
        departamentos_validos = [
            dep for dep in por_departamento if dep in pesos_departamento]
        pesos = [pesos_departamento[dep] for dep in departamentos_validos]
    else:
        departamentos_validos = list(por_departamento.keys())
        pesos = None

    filas = []
    for _ in range(n):
        dep = random.choices(departamentos_validos, weights=pesos, k=1)[0]
        # distrito uniforme dentro del departamento
        d = random.choice(por_departamento[dep])
        punto = punto_aleatorio_en_poligono(d["geometry"])
        filas.append(
            {
                "departamento": d["departamento"],
                "provincia": d["provincia"],
                "distrito": d["distrito"],
                "latitud": round(punto.y, 6),
                "longitud": round(punto.x, 6),
            }
        )
    return pd.DataFrame(filas)


if __name__ == "__main__":
    if not GEOJSON_PATH.exists():
        raise SystemExit(
            f"Descarga primero el GeoJSON real:\n"
            f"curl -o {GEOJSON_PATH} {GEOJSON_URL}"
        )

    distritos = cargar_distritos()
    print(f"Distritos reales cargados: {len(distritos)}")

    df = generar_ubicaciones(n=10, distritos=distritos)
    print(df.to_string(index=False))
    df.to_csv(Path(__file__).parent /
              "salida_ubicaciones_demo.csv", index=False)
