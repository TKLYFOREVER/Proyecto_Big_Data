"""
Ejecutar:
    python 04_pipeline_integrador.py --n 500
"""

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd

DIR = Path(__file__).parent


def _cargar_modulo(nombre_archivo: str):

    ruta = DIR / nombre_archivo
    spec = importlib.util.spec_from_file_location(nombre_archivo[:-3], ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo
    spec.loader.exec_module(modulo)
    return modulo


geoloc = _cargar_modulo("01_geolocalizacion.py")
tabular = _cargar_modulo("02_data_tabular.py")
texto = _cargar_modulo("03_texto_descripcion.py")


PESOS_DEPARTAMENTO_REALES = {
    "LIMA": 34.8,
    "LAMBAYEQUE": 7.9,
    "LA LIBERTAD": 6.6,
    "AREQUIPA": 6.4,
    "JUNIN": 4.4,
    "CUSCO": 3.8,
    "CALLAO": 3.2,
    "ICA": 3.1,
    "ANCASH": 2.7,
    "LORETO": 1.8,
    "AYACUCHO": 1.7,
    "HUANUCO": 2.1,
    "CAJAMARCA": 2.4,
    "APURIMAC": 0.9,
    "AMAZONAS": 0.9,
    "MADRE DE DIOS": 0.8,
    "HUANCAVELICA": 0.4,
    "MOQUEGUA": 0.6,
}


def construir_pesos_por_departamento(distritos: list[dict]) -> dict:
    deptos_geojson = sorted({d["departamento"] for d in distritos})
    suma_reales = sum(PESOS_DEPARTAMENTO_REALES.get(d, 0)
                      for d in deptos_geojson)
    faltantes = [
        d for d in deptos_geojson if d not in PESOS_DEPARTAMENTO_REALES]
    peso_residual_total = max(0.0, 100.0 - suma_reales)
    peso_residual_cada_uno = peso_residual_total / \
        len(faltantes) if faltantes else 0.0

    pesos = dict(PESOS_DEPARTAMENTO_REALES)
    for d in faltantes:
        pesos[d] = peso_residual_cada_uno
    return {d: pesos[d] for d in deptos_geojson}


def generar_pipeline(n: int, seed: int = 42) -> pd.DataFrame:
    geojson_path = DIR / "peru_distrital_simple.geojson"
    if not geojson_path.exists():
        raise SystemExit(
            f"Falta el GeoJSON real. Descárgalo con:\n"
            f"curl -o {geojson_path} {geoloc.GEOJSON_URL}"
        )
    distritos = geoloc.cargar_distritos(geojson_path)
    pesos_departamento = construir_pesos_por_departamento(distritos)
    df_geo = geoloc.generar_ubicaciones(
        n=n, distritos=distritos, pesos_departamento=pesos_departamento, seed=seed)

    semilla = tabular.construir_semilla(n_semilla=max(500, n), seed=seed)
    try:
        df_tab, _ = tabular.generar_con_sdv(semilla, n=n, seed=seed)
    except ImportError:
        df_tab = semilla.sample(
            n=n, replace=True, random_state=seed).reset_index(drop=True)

    df = pd.concat([df_geo.reset_index(drop=True),
                   df_tab.reset_index(drop=True)], axis=1)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])

    df["descripcion"] = texto.generar_descripciones(df, seed=seed)

    columnas_finales = [
        "departamento", "provincia", "distrito", "latitud", "longitud", "fecha_hora",
        "descripcion", "categoria_inei", "clasificacion_delito",
        "gravedad"
    ]
    return df[columnas_finales]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--salida", type=str,
                        default="data_delitos_sintetica.csv")
    parser.add_argument("--chunk_size", type=int, default=100000)
    args = parser.parse_args()

    salida = DIR / args.salida
    total_generar = args.n
    chunk = args.chunk_size

    if salida.exists():
        salida.unlink()

    filas_acumuladas = 0
    primera_iteracion = True

    while filas_acumuladas < total_generar:
        n_actual = min(chunk, total_generar - filas_acumuladas)
        seed_iter = args.seed + filas_acumuladas

        df_chunk = generar_pipeline(n=n_actual, seed=seed_iter)

        df_chunk.to_csv(salida, mode='a', index=False,
                        header=primera_iteracion)
        primera_iteracion = False

        filas_acumuladas += n_actual
        print(
            f"Progreso: {filas_acumuladas:,} / {total_generar:,} registros escritos...")

    print(
        f"\nFinalizado con éxito: {salida} ({salida.stat().st_size / (1024**3):.2f} GB)")
