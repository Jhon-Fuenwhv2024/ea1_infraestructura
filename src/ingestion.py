"""
EA1 - Ingesta de datos desde Open Brewery DB hacia MySQL.

Curso: Infraestructura y arquitectura para Big Data
Código: PREICA2602B010136
Institución: IU Digital de Antioquia
Docente: CESAR LUIS VASQUEZ
Estudiante: Jhon Jairo Fuentes Turizo

Ejecutar desde la raíz del repositorio:
    python src/ingestion.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pymysql
import requests
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

# ---------------------------------------------------------------------------
# Rutas del proyecto (independientes del cwd relativo)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
XLSX_DIR = SRC / "xlsx"
AUDIT_DIR = SRC / "static" / "auditoria"
DB_DIR = SRC / "db"

API_URL = "https://api.openbrewerydb.org/v1/breweries"
PER_PAGE = 200
MAX_PAGES = 100  # límite de seguridad; el catálogo público supera los 10k registros

API_TO_DB = {
    "id": "id",
    "name": "nombre",
    "brewery_type": "tipo_cerveza",
    "address_1": "direccion_1",
    "address_2": "direccion_2",
    "address_3": "direccion_3",
    "city": "ciudad",
    "state_province": "estado_provincia",
    "postal_code": "codigo_postal",
    "country": "pais",
    "longitude": "longitud",
    "latitude": "latitud",
    "phone": "telefono",
    "website_url": "sitio_web",
    "state": "estado",
    "street": "direccion_4",
}
DB_COLUMNS = list(API_TO_DB.values())
DB_TO_API = {db_name: api_name for api_name, db_name in API_TO_DB.items()}


def load_config() -> dict[str, Any]:
    """Carga variables de entorno (archivo .env)."""
    load_dotenv(ROOT / ".env")
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "ea1_ingestion_db"),
    }


def fetch_cervecerias() -> list[dict[str, Any]]:
    """Extrae cervecerías de la API con paginación (per_page=200)."""
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "User-Agent": "ea1-ingestion/1.0"})
    all_rows: list[dict[str, Any]] = []

    for page in range(1, MAX_PAGES + 1):
        params = {"per_page": PER_PAGE, "page": page}
        try:
            response = session.get(API_URL, params=params, timeout=60)
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(
                f"Error HTTP al consultar la API (página {page}): {exc}"
            ) from exc
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Error de red al consultar la API (página {page}): {exc}"
            ) from exc

        batch = response.json()
        if not isinstance(batch, list):
            raise RuntimeError(f"Respuesta inesperada de la API en página {page}: {type(batch)}")
        if not batch:
            break

        all_rows.extend(batch)
        print(f"  Página {page}: {len(batch)} registros (acumulado: {len(all_rows)})")

        if len(batch) < PER_PAGE:
            break

    if not all_rows:
        raise RuntimeError("La API no devolvió registros.")

    # Deduplicar por id por si la paginación se solapa
    unique: dict[str, dict[str, Any]] = {}
    for row in all_rows:
        rid = row.get("id")
        if rid:
            unique[str(rid)] = row

    records = list(unique.values())
    print(f"Total extraído de la API (únicos): {len(records)}")
    return records


def connect_server(cfg: dict[str, Any]) -> pymysql.Connection:
    """Conecta al servidor MySQL sin seleccionar base de datos."""
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


def ensure_database(cfg: dict[str, Any]) -> None:
    """Crea la base de datos si no existe."""
    conn = connect_server(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        print(f"Base de datos asegurada: {cfg['database']}")
    finally:
        conn.close()


def connect_db(cfg: dict[str, Any]) -> pymysql.Connection:
    """Conecta a la base de datos de trabajo."""
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def create_table(conn: pymysql.Connection) -> None:
    """Crea la tabla principal de cervecerías."""
    ddl = """
    CREATE TABLE IF NOT EXISTS cerveceria (
        id              VARCHAR(64)  NOT NULL,
        nombre            VARCHAR(255) NULL,
        tipo_cerveza   VARCHAR(64)  NULL,
        direccion_1       VARCHAR(255) NULL,
        direccion_2       VARCHAR(255) NULL,
        direccion_3       VARCHAR(255) NULL,
        ciudad            VARCHAR(128) NULL,
        estado_provincia  VARCHAR(128) NULL,
        codigo_postal     VARCHAR(32)  NULL,
        pais         VARCHAR(128) NULL,
        longitud       DOUBLE       NULL,
        latitud        DOUBLE       NULL,
        telefono           VARCHAR(64)  NULL,
        sitio_web     VARCHAR(512) NULL,
        estado           VARCHAR(128) NULL,
        direccion_4          VARCHAR(255) NULL,
        ingerido_en     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()
    print("Tabla 'cerveceria' asegurada.")


def _normalize(row: dict[str, Any]) -> tuple[Any, ...]:
    """Normaliza un registro de la API al orden exacto de columnas de la tabla."""
    values: list[Any] = []
    for db_col in DB_COLUMNS:
        api_col = DB_TO_API.get(db_col, db_col)
        val = row.get(api_col)
        if api_col in ("longitude", "latitude"):
            if val is None or val == "":
                values.append(None)
            else:
                try:
                    values.append(float(val))
                except (TypeError, ValueError):
                    values.append(None)
        else:
            if val is None:
                values.append(None)
            else:
                text = str(val).strip()
                values.append(text if text else None)
    return tuple(values)


def upsert_records(conn: pymysql.Connection, records: list[dict[str, Any]]) -> int:
    """Inserta o actualiza registros (idempotente vía ON DUPLICATE KEY UPDATE)."""
    placeholders = ", ".join(["%s"] * len(DB_COLUMNS))
    col_list = ", ".join(f"`{c}`" for c in DB_COLUMNS)
    updates = ", ".join(f"`{c}` = VALUES(`{c}`)" for c in DB_COLUMNS if c != "id")
    sql = (
        f"INSERT INTO cerveceria ({col_list}) VALUES ({placeholders}) "
        f"ON DUPLICATE KEY UPDATE {updates}"
    )

    data = [_normalize(r) for r in records]
    with conn.cursor() as cur:
        cur.executemany(sql, data)
    conn.commit()
    print(f"Registros upserted en MySQL: {len(data)}")
    return len(data)


def read_db_rows(conn: pymysql.Connection) -> list[dict[str, Any]]:
    """Lee todos los registros de la tabla cerveceria."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, nombre, tipo_cerveza, direccion_1, direccion_2, direccion_3, "
            "ciudad, estado_provincia, codigo_postal, pais, longitud, latitud, "
            "telefono, sitio_web, estado, direccion_4 FROM cerveceria"
        )
        rows = list(cur.fetchall())
    return rows


def export_xlsx(db_rows: list[dict[str, Any]], sample_size: int = 500) -> Path:
    """Exporta una muestra representativa a Excel con openpyxl."""
    XLSX_DIR.mkdir(parents=True, exist_ok=True)
    out = XLSX_DIR / "ingestion.xlsx"
    df = pd.DataFrame(db_rows)
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42).sort_values("id")
    df.to_excel(out, index=False, engine="openpyxl")
    print(f"Excel generado: {out} ({len(df)} filas)")
    return out


def write_audit(
    api_records: list[dict[str, Any]],
    db_rows: list[dict[str, Any]],
) -> Path:
    """Compara API vs MySQL y escribe el archivo de auditoría."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / "ingestion.txt"

    api_by_id = {str(r["id"]): r for r in api_records if r.get("id")}
    db_by_id = {str(r["id"]): r for r in db_rows if r.get("id")}

    api_ids = set(api_by_id)
    db_ids = set(db_by_id)
    missing_in_db = sorted(api_ids - db_ids)
    extra_in_db = sorted(db_ids - api_ids)
    common = api_ids & db_ids

    key_fields = [
        ("name", "nombre"),
        ("brewery_type", "tipo_cerveza"),
        ("city", "ciudad"),
        ("country", "pais"),
        ("state_province", "estado_provincia"),
    ]
    mismatches: list[str] = []
    for rid in sorted(common):
        api_row = api_by_id[rid]
        db_row = db_by_id[rid]
        for api_field, db_field in key_fields:
            api_val = api_row.get(api_field)
            db_val = db_row.get(db_field)
            api_norm = None if api_val is None or str(api_val).strip() == "" else str(api_val).strip()
            db_norm = None if db_val is None or str(db_val).strip() == "" else str(db_val).strip()
            if api_norm != db_norm:
                mismatches.append(
                    f"  - id={rid} API[{api_field}]={api_norm!r} | DB[{db_field}]={db_norm!r}"
                )

    counts_match = len(api_ids) == len(db_ids) and not missing_in_db and not extra_in_db
    fields_ok = len(mismatches) == 0
    integrity_ok = counts_match and fields_ok

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "============================================================",
        "AUDITORÍA DE INGESTA - EA1",
        "Proyecto: Infraestructura y arquitectura para Big Data",
        "Estudiante: Jhon Jairo Fuentes Turizo",
        "Fuente: Open Brewery DB (https://api.openbrewerydb.org/v1/breweries)",
        "Motor de almacenamiento: MySQL",
        "============================================================",
        f"Marca de tiempo: {ts}",
        "",
        "1. CONTEOS",
        f"   Registros extraídos de la API : {len(api_ids)}",
        f"   Registros almacenados en MySQL: {len(db_ids)}",
        f"   ¿Coinciden los conteos?       : {'SÍ' if counts_match else 'NO'}",
        "",
        "2. INTEGRIDAD DE CAMPOS CLAVE",
        "   Campos comparados: name↔nombre, brewery_type↔tipo_cerveza, city↔ciudad, country↔pais, state_province↔estado_provincia",
        f"   Registros comunes : {len(common)}",
        f"   Discrepancias     : {len(mismatches)}",
        f"   ¿Campos coinciden?: {'SÍ' if fields_ok else 'NO'}",
    ]

    if mismatches:
        lines.append("   Detalle (máx. 50):")
        lines.extend(mismatches[:50])
    else:
        lines.append("   Sin discrepancias en campos clave.")

    lines.extend(
        [
            "",
            "3. IDENTIFICADORES FALTANTES / EXTRA",
            f"   IDs en API ausentes en MySQL: {len(missing_in_db)}",
        ]
    )
    if missing_in_db:
        lines.append("   Lista (máx. 50): " + ", ".join(missing_in_db[:50]))
    else:
        lines.append("   Ninguno.")

    lines.append(f"   IDs en MySQL no presentes en API: {len(extra_in_db)}")
    if extra_in_db:
        lines.append("   Lista (máx. 50): " + ", ".join(extra_in_db[:50]))
    else:
        lines.append("   Ninguno.")

    lines.extend(
        [
            "",
            "4. CONFIRMACIÓN DE INTEGRIDAD",
            f"   Resultado: {'INTEGRIDAD CONFIRMADA' if integrity_ok else 'INTEGRIDAD NO CONFIRMADA'}",
            "   Criterio: mismos IDs entre API y MySQL + igualdad en campos clave.",
            "",
            "5. NOTAS",
            "   - Operación de carga: INSERT ... ON DUPLICATE KEY UPDATE (idempotente).",
            "============================================================",
        ]
    )

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Auditoría generada: {out}")
    print(f"Integridad: {'OK' if integrity_ok else 'FALLÓ'}")
    return out


def dump_sql(cfg: dict[str, Any]) -> Path | None:
    """Intenta generar un volcado SQL con mysqldump si está disponible."""
    import shutil
    import subprocess

    DB_DIR.mkdir(parents=True, exist_ok=True)
    out = DB_DIR / "ingestion.sql"
    mysqldump = shutil.which("mysqldump")
    if not mysqldump:
        print("mysqldump no está en PATH; se omite el dump local (CI lo generará).")
        return None

    cmd = [
        mysqldump,
        f"--host={cfg['host']}",
        f"--port={cfg['port']}",
        f"--user={cfg['user']}",
        "--single-transaction",
        "--routines",
        "--databases",
        cfg["database"],
    ]
    env = os.environ.copy()
    # Password vacío es válido (XAMPP); MYSQL_PWD evita prompt
    env["MYSQL_PWD"] = cfg["password"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            print(f"Advertencia mysqldump: {result.stderr.strip()}")
            return None
        out.write_text(result.stdout, encoding="utf-8")
        print(f"Dump SQL generado: {out}")
        return out
    except OSError as exc:
        print(f"No se pudo ejecutar mysqldump: {exc}")
        return None


def main() -> int:
    print("=== EA1 Ingesta Open Brewery DB -> MySQL ===")
    cfg = load_config()
    print(
        f"MySQL destino: {cfg['user']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    )

    print("\n[1/5] Extracción desde la API...")
    api_records = fetch_cervecerias()

    print("\n[2/5] Conexión y preparación de MySQL...")
    ensure_database(cfg)
    conn = connect_db(cfg)
    try:
        create_table(conn)
        print("\n[3/5] Carga / upsert en MySQL...")
        upsert_records(conn, api_records)
        db_rows = read_db_rows(conn)
    finally:
        conn.close()

    print(f"Filas leídas desde MySQL: {len(db_rows)}")

    print("\n[4/5] Exportación Excel (muestra)...")
    export_xlsx(db_rows)

    print("\n[5/5] Auditoría API vs MySQL...")
    write_audit(api_records, db_rows)

    dump_sql(cfg)

    print("\nProceso de ingesta finalizado correctamente.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - superficie clara para la entrega
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc