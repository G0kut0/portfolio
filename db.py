"""Acceso a SQLite: conexión por petición, inicialización y datos de ejemplo."""
import os
import sqlite3

from flask import g

BASE = os.path.dirname(os.path.abspath(__file__))


def get_db():
    if "db" not in g:
        from flask import current_app
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(path):
    """Crea las tablas (si no existen)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    with open(os.path.join(BASE, "schema.sql"), encoding="utf-8") as f:
        con.executescript(f.read())
    con.commit()
    con.close()


PROYECTOS = [
    ("Cyberdeck",
     "Dispositivo portátil de monitorización basado en Raspberry Pi.",
     "Cyberdeck portátil de monitorización. Una Raspberry Pi 3B hace de "
     "ordenador principal, un Arduino Nano lee los sensores y una Pi Zero W "
     "actúa como nodo auxiliar. Aquí se explica la arquitectura de hardware "
     "(alimentación, buses, sensores) y de software (servicios, comunicación "
     "entre placas y panel de monitorización).",
     "Raspberry Pi 3B, Arduino Nano, Pi Zero W", "hardware", "", "", "", "2025-01-01", 1),
    ("Simulador TLAP (TFB)",
     "Mi trabajo de fin de bachiller y la calculadora de rendimientos basada en él.",
     "Trabajo de fin de bachiller sobre la transmisión láser de alta potencia "
     "(TLAP). Estima qué parte de la potencia de un láser se convierte en "
     "electricidad en la Tierra, Marte y la Luna. La versión original está en "
     "Python y la calculadora web interactiva permite cambiar temperatura, "
     "potencia, eficiencia cuántica y resistencia de la célula.",
     "Python, JavaScript, SVG", "informatica", "", "/calculadora/", "", "2025-06-01", 1),
    ("Juego de preguntas de anime",
     "Trivia de estética cyberpunk para tres jugadores.",
     "Juego de preguntas sobre anime con estética cyberpunk, pensado para "
     "jugar entre tres personas en un mismo dispositivo.",
     "HTML, JavaScript", "informatica", "", "", "", "2025-03-01", 0),
    ("Juego de misterio (asesinato)",
     "Juego local para 9 jugadores con fichas privadas y pistas.",
     "Juego de misterio de asesinato para nueve jugadores en local: cada "
     "jugador recibe una ficha privada con su personaje y se van revelando "
     "pistas durante la partida.",
     "HTML, JavaScript", "informatica", "", "", "", "2025-04-01", 0),
    ("Poker Night",
     "Simulador de fichas para una mesa cash 2/5.",
     "Aplicación web para gestionar las fichas de una mesa de cash 2/5: "
     "compras, bote y reparto.",
     "Web app", "informatica", "", "", "", "2025-05-01", 0),
    ("Draft por subasta",
     "Reglas, equipos de 5 y presupuesto por jugador.",
     "Aplicación para organizar un draft por subasta: reglas, equipos de "
     "cinco jugadores y presupuesto por participante.",
     "Web app", "informatica", "", "", "", "2025-07-01", 0),
    ("Cifras y Letras",
     "Buscador de la combinación exacta o más cercana a un objetivo.",
     "Aplicación local que busca la combinación de operaciones que alcanza "
     "exactamente un objetivo, o la más cercana si no existe.",
     "App local", "informatica", "", "", "", "2025-08-01", 0),
    ("Mod de reloj NH35",
     "Mi primer mod de relojería con movimiento NH35.",
     "Mi primer mod de reloj con movimiento automático NH35: elección de "
     "piezas, montaje y ajuste.",
     "Hardware, relojería", "hardware", "", "", "", "2025-09-01", 0),
]

HABILIDADES = [
    ("Arduino", "Hardware", 4), ("Raspberry Pi", "Hardware", 4),
    ("Electrónica básica", "Hardware", 3),
    ("Python", "Programación", 4), ("JavaScript", "Programación", 3),
    ("HTML/CSS", "Programación", 4),
    ("Joomla", "Web", 3), ("Flask + SQLite", "Web", 3),
    ("Git", "Herramientas", 3), ("Neovim", "Herramientas", 3),
    ("Linux", "Herramientas", 3),
    ("Cohetería de modelismo", "Otras", 3), ("Fotografía", "Otras", 3),
]

FORMACION = [
    ("Universidad de Granada", "Grado en Física", "2025", "", "En curso."),
    ("IES Santa Catalina de Alejandría (Jaén)", "Bachillerato", "", "2025",
     "Mención por el TFB sobre transmisión láser de alta potencia (TLAP)."),
]

LOGROS = [
    ("Natación: 50 m libres", "Añade aquí tu marca personal.", "natacion", ""),
    ("Natación: 100 m libres", "Objetivo: bajar de 1:00.", "natacion", ""),
    ("TFB defendido", "Trabajo fin de bachiller sobre TLAP.", "hitos", "2025"),
    ("Proyectos terminados", "Cyberdeck, juegos, simuladores y más.", "hitos", ""),
]


def seed_db(path, nombre_admin, password_hash):
    """Rellena una base de datos vacía con el contenido inicial."""
    con = sqlite3.connect(path)
    cur = con.cursor()
    if not cur.execute("SELECT 1 FROM perfil").fetchone():
        cur.execute(
            "INSERT INTO perfil (id, nombre, titular, bio, ubicacion, email, github)"
            " VALUES (1, ?, ?, ?, ?, ?, ?)",
            ("José Antonio",
             "Estudiante de Física en la UGR · Sistemas embebidos y desarrollo web",
             "Estudiante de Física, nadador de velocidad libre y aficionado al "
             "hardware (Arduino, Raspberry Pi). Me gusta construir cosas que "
             "mezclan electrónica y software.",
             "Granada", "tuweb@gmail.com", "https://github.com/"))
        cur.executemany(
            "INSERT INTO proyectos (titulo, descripcion_corta, descripcion_larga,"
            " tecnologias, categoria, repo_url, demo_url, imagen, fecha, destacado)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)", PROYECTOS)
        cur.executemany(
            "INSERT INTO habilidades (nombre, categoria, nivel) VALUES (?,?,?)", HABILIDADES)
        cur.executemany(
            "INSERT INTO formacion (centro, titulacion, fecha_inicio, fecha_fin,"
            " descripcion) VALUES (?,?,?,?,?)", FORMACION)
        cur.executemany(
            "INSERT INTO logros (titulo, descripcion, categoria, fecha) VALUES (?,?,?,?)",
            LOGROS)
    if nombre_admin:
        cur.execute(
            "INSERT OR IGNORE INTO usuarios_admin (usuario, password_hash) VALUES (?, ?)",
            (nombre_admin, password_hash))
    con.commit()
    con.close()
