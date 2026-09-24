from datetime import datetime, timedelta
import random

import pandas as pd

PROPORCIONES_INEI_2023 = {
    "Contra el patrimonio": 375_673,
    "Contra la seguridad pública": 68_725,
    "Contra la vida, el cuerpo y la salud": 49_303,
    "Contra la libertad": 41_744,
    "Otros": 19_783,
}

SUBCATEGORIAS = {
    "Contra el patrimonio": [
        ("Robo", "alta"), ("Hurto", "media"), ("Robo agravado",
                                               "alta"), ("Estafa", "baja"),
    ],
    "Contra la vida, el cuerpo y la salud": [
        ("Homicidio", "alta"), ("Lesiones", "media"),
    ],
    "Contra la seguridad pública": [
        ("Terrorismo", "alta"), ("Tenencia ilegal de armas",
                                 "alta"), ("Tráfico de drogas", "media"),
    ],
    "Contra la libertad": [
        ("Secuestro", "alta"), ("Violación", "alta"), ("Amenazas", "media"),
    ],
    "Otros": [
        ("Otros", "baja"),
    ],
}


def construir_semilla(n_semilla: int = 500, seed: int = 42) -> pd.DataFrame:
    """Construye la tabla semilla respetando las proporciones reales de INEI."""
    random.seed(seed)
    total = sum(PROPORCIONES_INEI_2023.values())
    filas = []
    inicio = datetime(2025, 1, 1)
    for categoria, count in PROPORCIONES_INEI_2023.items():
        n_categoria = round(n_semilla * count / total)
        subcats = SUBCATEGORIAS[categoria]
        for _ in range(n_categoria):
            subcat, gravedad = random.choice(subcats)
            fecha = inicio + timedelta(
                days=random.randint(0, 364),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            filas.append(
                {
                    "categoria_inei": categoria,
                    "clasificacion_delito": subcat,
                    "gravedad": gravedad,
                    "fecha_hora": fecha,
                }
            )
    return pd.DataFrame(filas)


def generar_con_sdv(semilla: pd.DataFrame, n: int, seed: int = 42):

    from sdv.metadata import SingleTableMetadata
    from sdv.single_table import GaussianCopulaSynthesizer

    df = semilla.copy()
    df["combo"] = (
        df["categoria_inei"] + "||" +
        df["clasificacion_delito"] + "||" + df["gravedad"]
    )
    df_sdv = df[["combo", "fecha_hora"]].copy()
    df_sdv["fecha_hora"] = df_sdv["fecha_hora"].dt.strftime(
        "%Y-%m-%d %H:%M:%S")

    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df_sdv)
    metadata.update_column(column_name="fecha_hora",
                           sdtype="datetime", datetime_format="%Y-%m-%d %H:%M:%S")
    metadata.update_column(column_name="combo", sdtype="categorical")

    synthesizer = GaussianCopulaSynthesizer(metadata)
    synthesizer.fit(df_sdv)
    sinteticos = synthesizer.sample(num_rows=n)

    partes = sinteticos["combo"].str.split(r"\|\|", expand=True)
    sinteticos["categoria_inei"] = partes[0]
    sinteticos["clasificacion_delito"] = partes[1]
    sinteticos["gravedad"] = partes[2]
    sinteticos = sinteticos.drop(columns=["combo"])
    return sinteticos, synthesizer


if __name__ == "__main__":
    semilla = construir_semilla(n_semilla=500)
    print("Semilla (primeras filas):")
    print(semilla.head(10).to_string(index=False))
    print(f"\nTotal filas semilla: {len(semilla)}")
    print("\nDistribución por categoría INEI en la semilla:")
    print((semilla["categoria_inei"].value_counts(
        normalize=True) * 100).round(1))

    sinteticos, _ = generar_con_sdv(semilla, n=20)
    print("\nMuestra generada por SDV (Gaussian Copula):")
    print(sinteticos.head(10).to_string(index=False))
