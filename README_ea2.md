# EA2 — Limpieza de datos (Infraestructura Big Data)

**Curso:** PREICA2602B010136  
**Estudiante:** Jhon Jairo Fuentes Turizo  
**Entrega:** EA2 — Limpieza y auditoría de datos  
**Repositorio base (EA1):** [ea1_infraestructura](https://github.com/Jhon-Fuenwhv2024/ea1_infraestructura)

## Descripción

Este paquete ejecuta el pipeline de **limpieza de datos** sobre la base SQLite `src/db/ingestion.db` (tabla `cerveceria`). Esa base simula el almacenamiento en la nube construido en EA1 a partir de la API **Open Brewery DB**, incluyendo filas “sucias” (duplicados, nulos, tipos incorrectos, variantes de `tipo_cerveza`) para practicar calidad de datos.

Salidas esperadas:

| Artefacto | Ruta |
|-----------|------|
| Excel limpio | `src/xlsx/cleaned_data.xlsx` |
| Reporte de auditoría | `src/static/auditoria/cleaning_report.txt` |

## Estructura

```
Fuentes_Jhon/
├── setup.py
├── requirements.txt
├── README.md
├── .github/workflows/bigdata.yml
└── src/
    ├── cleaning.py
    ├── db/ingestion.db
    ├── xlsx/cleaned_data.xlsx
    └── static/auditoria/cleaning_report.txt
```

## Requisitos

- Python 3.11+
- Dependencias: `pandas`, `openpyxl`

## Clonar e instalar

```bash
git clone https://github.com/Jhon-Fuenwhv2024/ea1_infraestructura.git
cd ea1_infraestructura
# Si este paquete vive en una carpeta Fuentes_Jhon dentro del repo:
cd Fuentes_Jhon   # ajustar si la carpeta raíz del zip se descomprime aquí

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# opcional:
pip install -e .
```

## Ejecutar la limpieza

```bash
python src/cleaning.py
```

El script:

1. Carga `cerveceria` desde `src/db/ingestion.db`
2. Explora estadísticas (filas, nulos, duplicados, tipos)
3. Elimina duplicados, convierte `longitud`/`latitud` a float, normaliza `tipo_cerveza`, maneja nulos
4. Genera `src/xlsx/cleaned_data.xlsx` y `src/static/auditoria/cleaning_report.txt`

## GitHub Actions

El workflow `.github/workflows/bigdata.yml`:

- Se dispara en `push` / `pull_request` / `workflow_dispatch`
- Configura Python 3.11
- Instala dependencias
- Ejecuta `python src/cleaning.py`
- Verifica que el Excel y el reporte existan y no estén vacíos
- Sube ambos archivos como artefactos (`ea2-cleaned-data`)

## Linaje de datos (EA1 → EA2)

- **EA1:** extracción desde Open Brewery DB e ingestión hacia almacenamiento simulado en la nube (SQLite local `ingestion.db`).
- **EA2:** este proyecto — limpieza, tipado, normalización y auditoría reproducibles vía script + CI.

## Autor

Jhon Jairo Fuentes Turizo — PREICA2602B010136
