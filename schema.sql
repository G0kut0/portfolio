-- Esquema de la base de datos del portfolio (SQLite)

PRAGMA foreign_keys = ON;

-- 1. perfil: una sola fila (id = 1)
CREATE TABLE IF NOT EXISTS perfil (
    id          INTEGER PRIMARY KEY CHECK (id = 1),
    nombre      TEXT NOT NULL,
    titular     TEXT NOT NULL DEFAULT '',
    bio         TEXT NOT NULL DEFAULT '',
    ubicacion   TEXT NOT NULL DEFAULT '',
    foto        TEXT NOT NULL DEFAULT '',   -- nombre de archivo subido o URL
    cv          TEXT NOT NULL DEFAULT '',   -- PDF subido o URL
    email       TEXT NOT NULL DEFAULT '',
    github      TEXT NOT NULL DEFAULT '',
    linkedin    TEXT NOT NULL DEFAULT '',
    instagram   TEXT NOT NULL DEFAULT '',
    otra_red    TEXT NOT NULL DEFAULT ''
);

-- 2. proyectos
CREATE TABLE IF NOT EXISTS proyectos (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo             TEXT NOT NULL,
    descripcion_corta  TEXT NOT NULL DEFAULT '',
    descripcion_larga  TEXT NOT NULL DEFAULT '',
    tecnologias        TEXT NOT NULL DEFAULT '',   -- separadas por comas
    categoria          TEXT NOT NULL DEFAULT 'informatica'
                       CHECK (categoria IN ('informatica', 'hardware')),
    repo_url           TEXT NOT NULL DEFAULT '',
    demo_url           TEXT NOT NULL DEFAULT '',
    imagen             TEXT NOT NULL DEFAULT '',
    fecha              TEXT NOT NULL DEFAULT '',   -- AAAA-MM-DD
    destacado          INTEGER NOT NULL DEFAULT 0 CHECK (destacado IN (0, 1)),
    visible            INTEGER NOT NULL DEFAULT 1 CHECK (visible IN (0, 1))
);

-- 3. habilidades
CREATE TABLE IF NOT EXISTS habilidades (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    categoria  TEXT NOT NULL,
    nivel      INTEGER NOT NULL DEFAULT 3 CHECK (nivel BETWEEN 1 AND 5)
);

-- 4. formacion
CREATE TABLE IF NOT EXISTS formacion (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    centro        TEXT NOT NULL,
    titulacion    TEXT NOT NULL,
    fecha_inicio  TEXT NOT NULL DEFAULT '',
    fecha_fin     TEXT NOT NULL DEFAULT '',      -- vacío = en curso
    descripcion   TEXT NOT NULL DEFAULT ''
);

-- 5. logros
CREATE TABLE IF NOT EXISTS logros (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo       TEXT NOT NULL,
    descripcion  TEXT NOT NULL DEFAULT '',
    categoria    TEXT NOT NULL DEFAULT 'otros',
    fecha        TEXT NOT NULL DEFAULT ''
);

-- 6. mensajes_contacto (los rellenan los visitantes)
CREATE TABLE IF NOT EXISTS mensajes_contacto (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre   TEXT NOT NULL,
    email    TEXT NOT NULL,
    mensaje  TEXT NOT NULL,
    fecha    TEXT NOT NULL DEFAULT (datetime('now')),
    leido    INTEGER NOT NULL DEFAULT 0 CHECK (leido IN (0, 1))
);

-- 7. usuarios_admin
CREATE TABLE IF NOT EXISTS usuarios_admin (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario        TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,                -- bcrypt
    ultimo_acceso  TEXT
);
