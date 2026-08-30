# EA1 – Ingesta de datos desde una API

**Curso:** Infraestructura y arquitectura para Big Data  
**Código:** PREICA2602B010136  
**Institución:** IU Digital de Antioquia  
**Docente:** CESAR LUIS VASQUEZ  
**Estudiante:** Jhon Jairo Fuentes Turizo  
**Entrega:** Actividad EA1 – etapa de ingesta del proyecto integrador  

---

## 1. Descripción de la solución

Este repositorio implementa la **etapa de ingesta de datos** del proyecto integrador de Big Data:

1. Extrae un volumen sustancial de registros desde una **API pública sin autenticación** (Open Brewery DB).
2. Los almacena en una base de datos **MySQL 8**.
3. Genera evidencias de entrega:
   - Muestra en Excel (`src/xlsx/ingestion.xlsx`)
   - Archivo de auditoría API vs MySQL (`src/static/auditoria/ingestion.txt`)
   - Esquema y dump SQL (`src/db/schema.sql`, `src/db/ingestion.sql`)
4. Automatiza el proceso con **GitHub Actions** (servicio MySQL + ejecución del script + artefactos).

### ¿Por qué MySQL / XAMPP en lugar de SQLite?

El material del curso recomienda **SQLite** para la evidencia local. En este trabajo se **sustituye SQLite por MySQL** de forma explícita  **MySQL mediante XAMPP en Windows**

| Aspecto | Curso (recomendado) | Esta entrega |
|---|---|---|
| Motor | SQLite (`ingestion.db`) | **MySQL 8** (XAMPP local / servicio en CI) |
| Evidencia de BD | Archivo `.db` | Dump `.sql` + verificación en Actions |
| Conexión local | Archivo embebido | `127.0.0.1:3306`, usuario `root`, contraseña vacía |

---

## 2. API utilizada

- **Nombre:** Open Brewery DB  
- **Endpoint:** `https://api.openbrewerydb.org/v1/breweries`  
- **Autenticación:** ninguna (sin API key)  
- **Paginación:** `per_page=200` y parámetro `page`  
- **Volumen:** se ingieren **miles** de cervecerías (corrida real ≈ **11 848** registros)  

Campos principales ingeridos: `id`, `name`, `brewery_type`, direcciones, `city`, `state_province`, `postal_code`, `country`, `longitude`, `latitude`, `phone`, `website_url`, `state`, `street`.
                            : `id`, `nombre`, `tipo_cervesa`, direcciones, `ciudad`, `estado_provincia`, `codigo_postal`, `pais`, `longitud`, `latitud`, `telefono`, `sitio_web`, `estado`, `direccion'.

---

## 3. Requisitos

- Python **3.11** (también compatible con 3.12 en pruebas locales)
- MySQL 8 (XAMPP en Windows, o MySQL Server / contenedor en otros entornos)
- Git

Dependencias Python (ver `requirements.txt`): `requests`, `pymysql`, `pandas`, `openpyxl`, `python-dotenv`.

---

## 4. Cómo clonar e instalar (Windows + XAMPP)

### 4.1 Clonar el repositorio

```bash
git clone https://github.com/Jhon-Fuenwhv2024/ea1_infraestructura.git
cd ea1_ingesta_datos
```

### 4.2 Crear y activar entorno virtual

```bash
python -m venv venv
# Windows (PowerShell / CMD):
venv\Scripts\activate
# Linux / macOS:
# source venv/bin/activate
```

### 4.3 Instalar dependencias

```bash
pip install -r requirements.txt
pip install -e .
```

### 4.4 Configurar variables de entorno para XAMPP

Copiar el ejemplo y ajustar si es necesario:

```bash
copy .env
# Linux/macOS: cp .env
```

Contenido esperado de `.env` (valores por defecto de XAMPP):

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=ea1_ingestion
```

> El archivo `.env` **no se sube al repositorio** (está en `.gitignore`). No hay secretos versionados.

### 4.5 Iniciar MySQL en XAMPP

1. Abrir el **Panel de control de XAMPP**.
2. Iniciar el módulo **MySQL** (puerto 3306).
3. Verificar que el servicio esté en verde / Running.

El script crea la base `ea1_ingestion_db` y la tabla `cerveceria` si no existen.

### 4.6 Ejecutar la ingesta

Desde la **raíz del proyecto**:

```bash
python src/ingestion.py
```

Salidas esperadas tras una corrida exitosa:

- Filas en MySQL (`ea1_ingestion.breweries`)
- `src/xlsx/ingestion.xlsx`
- `src/static/auditoria/ingestion.txt`
- `src/db/ingestion.sql` (si `mysqldump` está disponible en el PATH)

---

## 5. Automatización con GitHub Actions

El flujo está en `.github/workflows/bigdata.yml`.

**Disparadores:** `push` y `workflow_dispatch` (ejecución manual).

**Qué hace el workflow:**

1. Levanta un **servicio MySQL 8** (los runners de GitHub no ven el XAMPP).
2. Configura **Python 3.11** e instala dependencias.
3. Ejecuta `python src/ingestion.py` con las mismas variables `MYSQL_*` (en CI y en XAMPP local la contraseña suele ir vacía).
4. Verifica que MySQL tenga filas (>= 100).
5. Verifica que `ingestion.xlsx` e `ingestion.txt` existan y no estén vacíos.
6. Genera `mysqldump` → `src/db/ingestion.sql`.
7. Sube **artefactos**: Excel, auditoría y dump SQL.
---

## 6. Estructura del proyecto

```text
.
├── setup.py
├── README.md
├── .env.example
├── requirements.txt
├── .gitignore
├── .github/
│   └── workflows/
│       └── bigdata.yml
└── src/
    ├── ingestion.py
    ├── static/
    │   └── auditoria/
    │       └── ingestion.txt      # evidencia de auditoría (corrida real)
    ├── db/
    │   ├── schema.sql             # DDL MySQL
    │   └── ingestion.sql          # dump SQL (evidencia de BD)
    └── xlsx/
        └── ingestion.xlsx         # muestra Pandas/openpyxl
```

---

## 7. Confirmación de integridad

El archivo `src/static/auditoria/ingestion.txt` documenta:

- Marca de tiempo de la corrida
- Conteo de registros en la API vs MySQL
- Comparación de campos clave ("nombre", "tipo_cerveza", "ciudad", "pais", "estado_provincia")
- IDs faltantes o sobrantes
- Confirmación explícita: **INTEGRIDAD CONFIRMADA** / **NO CONFIRMADA**

La carga es **idempotente** (`INSERT ... ON DUPLICATE KEY UPDATE` sobre la PK `id`).
---

## 8. Notas técnicas

- Cliente MySQL: **PyMySQL**
- Excel: **pandas + openpyxl**
- HTTP: **requests**
- Empaquetado: `pip install -e .` mediante `setup.py`
- Python objetivo del curso/CI: **3.11**
