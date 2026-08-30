-- Esquema MySQL para la etapa de ingesta EA1
-- Fuente: Open Brewery DB (https://api.openbrewerydb.org/v1/breweries)
-- Motor: MySQL 8 (XAMPP en entorno local / servicio en GitHub Actions)

CREATE DATABASE IF NOT EXISTS ea1_ingestion_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ea1_ingestion_db;

CREATE TABLE IF NOT EXISTS cervecia (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
