"""Portfolio de José Antonio: web pública + panel de administración (CMS propio).

Python (Flask) y SQL (SQLite, consultas escritas a mano, sin ORM).

    flask --app app crear-admin     # crea o cambia el usuario administrador
    flask --app app run             # arranca la web en http://127.0.0.1:5000
"""
import hashlib
import os
import re
import secrets
import time
from functools import wraps

import bcrypt
import click
from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   send_from_directory, session, url_for)
from markupsafe import Markup, escape

from db import close_db, get_db, init_db, seed_db

BASE = os.path.dirname(os.path.abspath(__file__))
INSTANCE = os.path.join(BASE, "instance")
UPLOADS = os.path.join(BASE, "uploads")

EXT_IMAGEN = {"png", "jpg", "jpeg", "webp", "gif"}
EXT_PDF = {"pdf"}


# ---------------------------------------------------------------------------
# Definición de las secciones editables del CMS.
# Cada campo: (columna, etiqueta, tipo, opciones). Tipos: texto, largo, url,
# fecha, si_no, nivel, opcion, imagen. Añadir un campo aquí (y en schema.sql)
# basta para que aparezca en el panel.
# ---------------------------------------------------------------------------
ENTIDADES = {
    "proyectos": {
        "plural": "Proyectos", "singular": "proyecto",
        "orden": "destacado DESC, fecha DESC, id DESC",
        "lista": ["titulo", "categoria", "fecha", "destacado", "visible"],
        "campos": [
            ("titulo", "Título", "texto", {"obligatorio": True}),
            ("descripcion_corta", "Descripción corta", "texto",
             {"ayuda": "Una frase. Aparece en la tarjeta del proyecto."}),
            ("descripcion_larga", "Descripción larga", "largo",
             {"ayuda": "Aparece en la página del proyecto. Separa párrafos con una línea en blanco."}),
            ("tecnologias", "Tecnologías", "texto", {"ayuda": "Separadas por comas."}),
            ("categoria", "Categoría", "opcion",
             {"opciones": [("informatica", "Informática"), ("hardware", "Hardware y otros")]}),
            ("repo_url", "Enlace al repositorio", "url", {}),
            ("demo_url", "Enlace a la demo", "url",
             {"ayuda": "Dirección completa (https://…) o ruta interna (/calculadora/)."}),
            ("imagen", "Imagen", "imagen", {}),
            ("fecha", "Fecha", "fecha", {}),
            ("destacado", "Destacado", "si_no", {}),
            ("visible", "Visible en la web", "si_no", {"defecto": 1}),
        ],
    },
    "habilidades": {
        "plural": "Habilidades", "singular": "habilidad",
        "orden": "categoria, nivel DESC, nombre",
        "lista": ["nombre", "categoria", "nivel"],
        "campos": [
            ("nombre", "Nombre", "texto", {"obligatorio": True}),
            ("categoria", "Categoría", "texto",
             {"obligatorio": True,
              "ayuda": "Por ejemplo: Hardware, Programación, Web, Herramientas, Otras."}),
            ("nivel", "Nivel (1-5)", "nivel", {"defecto": 3}),
        ],
    },
    "formacion": {
        "plural": "Formación", "singular": "estudio",
        "orden": "fecha_inicio DESC, id",
        "lista": ["centro", "titulacion", "fecha_inicio", "fecha_fin"],
        "campos": [
            ("centro", "Centro", "texto", {"obligatorio": True}),
            ("titulacion", "Titulación", "texto", {"obligatorio": True}),
            ("fecha_inicio", "Inicio", "texto", {"ayuda": "Año o fecha, por ejemplo 2025."}),
            ("fecha_fin", "Fin", "texto", {"ayuda": "Déjalo vacío si sigue en curso."}),
            ("descripcion", "Descripción", "largo", {}),
        ],
    },
    "logros": {
        "plural": "Logros", "singular": "logro",
        "orden": "categoria DESC, fecha DESC, id",
        "lista": ["titulo", "categoria", "fecha"],
        "campos": [
            ("titulo", "Título", "texto", {"obligatorio": True}),
            ("descripcion", "Descripción", "largo", {}),
            ("categoria", "Categoría", "opcion",
             {"opciones": [("natacion", "Natación"), ("hitos", "Hitos"), ("otros", "Otros")]}),
            ("fecha", "Fecha", "texto", {"ayuda": "Año o fecha. Opcional."}),
        ],
    },
}

CAMPOS_PERFIL = [
    ("nombre", "Nombre", "texto", {"obligatorio": True}),
    ("titular", "Titular", "texto", {}),
    ("bio", "Bio corta", "largo", {"ayuda": "Dos o tres líneas."}),
    ("ubicacion", "Ubicación", "texto", {}),
    ("foto", "Foto", "imagen", {}),
    ("cv", "Currículum (PDF)", "pdf", {}),
    ("email", "Email", "email", {}),
    ("github", "GitHub", "url", {}),
    ("linkedin", "LinkedIn", "url", {}),
    ("instagram", "Instagram", "url", {}),
    ("otra_red", "Otra red o web", "url", {}),
]

RE_URL = re.compile(r"^(https?://\S+|/[^/\s]\S*|/)$")
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def crear_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.path.join(INSTANCE, "portfolio.db"),
        UPLOADS=UPLOADS,
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,   # 8 MB por subida
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIES_SEGURAS") == "1",
    )
    app.config.update(config or {})
    os.makedirs(INSTANCE, exist_ok=True)
    os.makedirs(app.config["UPLOADS"], exist_ok=True)
    app.secret_key = os.environ.get("SECRET_KEY") or _clave_secreta()

    # Detrás de un proxy (PythonAnywhere, nginx...) la IP real del visitante
    # llega en una cabecera. Solo se confía en ella si se pide con PROXY=1.
    if os.environ.get("PROXY") == "1":
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    init_db(app.config["DATABASE"])
    seed_db(app.config["DATABASE"], None, None)
    app.teardown_appcontext(close_db)

    intentos = {}   # clave por IP -> horas de los intentos: freno a abusos

    # ------------------------------------------------------------------ util
    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        return session["csrf"]

    @app.before_request
    def comprobar_csrf():
        if request.method == "POST":
            enviado = request.form.get("csrf", "").encode()
            esperado = session.get("csrf", "").encode()
            if not enviado or not secrets.compare_digest(enviado, esperado):
                abort(400, "Formulario caducado. Vuelve atrás y recarga la página.")

    @app.after_request
    def cabeceras_seguridad(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'; "
            "object-src 'none'; base-uri 'self'; form-action 'self'; "
            "frame-ancestors 'none'")
        if request.path.startswith("/admin"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    def demasiadas(clave, maximo, segundos):
        """Freno por IP en memoria: True si se ha superado el máximo."""
        ahora = time.time()
        if len(intentos) > 10000:      # no dejar crecer el registro sin límite
            intentos.clear()
        veces = [t for t in intentos.get(clave, []) if ahora - t < segundos]
        intentos[clave] = veces
        return len(veces) >= maximo

    def apuntar(clave):
        intentos.setdefault(clave, []).append(time.time())

    def borrar_archivo(valor):
        """Borra del disco una subida que ya no se usa."""
        if valor and not valor.startswith(("http://", "https://", "/")):
            try:
                os.remove(os.path.join(app.config["UPLOADS"], os.path.basename(valor)))
            except OSError:
                pass

    def limpiar_subidas(campos, antes, despues=None):
        for nombre, _etiqueta, tipo, _op in campos:
            if tipo in ("imagen", "pdf") and antes[nombre] != (despues or {}).get(nombre):
                borrar_archivo(antes[nombre])

    def media(valor):
        """Convierte lo guardado (archivo subido, URL o ruta) en un enlace."""
        if not valor:
            return ""
        if valor.startswith(("http://", "https://", "/")):
            return valor
        return url_for("archivo", nombre=valor)

    @app.template_filter("parrafos")
    def parrafos(texto):
        trozos = [t.strip() for t in re.split(r"\n\s*\n", texto or "") if t.strip()]
        return Markup("".join(
            "<p>%s</p>" % escape(t).replace("\n", Markup("<br>")) for t in trozos))

    @app.template_filter("lista")
    def lista(texto):
        return [t.strip() for t in (texto or "").split(",") if t.strip()]

    @app.context_processor
    def comunes():
        return {"csrf_token": csrf_token, "media": media, "entidades": ENTIDADES}

    def login_requerido(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not session.get("admin_id"):
                return redirect(url_for("login", siguiente=request.path))
            fila = get_db().execute(
                "SELECT id, usuario, ultimo_acceso, password_hash FROM usuarios_admin"
                " WHERE id = ?", (session["admin_id"],)).fetchone()
            if fila is None or session.get("sello") != sello(fila["password_hash"]):
                session.clear()
                return redirect(url_for("login"))
            g.admin = fila
            g.sin_leer = get_db().execute(
                "SELECT COUNT(*) FROM mensajes_contacto WHERE leido = 0").fetchone()[0]
            return vista(*args, **kwargs)
        return envoltura

    def guardar_archivo(archivo, extensiones):
        """Guarda una subida con nombre aleatorio. Devuelve el nombre o None."""
        ext = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
        if ext not in extensiones:
            return None
        nombre = "%s.%s" % (secrets.token_hex(12), ext)
        archivo.save(os.path.join(app.config["UPLOADS"], nombre))
        return nombre

    def leer_formulario(campos, actual=None):
        """Valida el formulario según la definición de campos.
        Devuelve (valores, errores)."""
        valores, errores = {}, {}
        for nombre, etiqueta, tipo, op in campos:
            if tipo in ("imagen", "pdf"):
                valor = (actual[nombre] if actual else "") or ""
                if request.form.get(nombre + "_quitar"):
                    valor = ""
                subida = request.files.get(nombre)
                if subida and subida.filename:
                    nuevo = guardar_archivo(subida, EXT_IMAGEN if tipo == "imagen" else EXT_PDF)
                    if nuevo is None:
                        errores[nombre] = ("Formato no admitido. Usa PNG, JPG, WEBP o GIF."
                                           if tipo == "imagen" else "El archivo debe ser un PDF.")
                    else:
                        valor = nuevo
                valores[nombre] = valor
                continue
            if tipo == "si_no":
                valores[nombre] = 1 if request.form.get(nombre) else 0
                continue
            valor = request.form.get(nombre, "").strip()
            if tipo != "largo":
                valor = valor.replace("\r", " ").replace("\n", " ")
            if op.get("obligatorio") and not valor:
                errores[nombre] = "Este campo es obligatorio."
            elif tipo == "url" and valor and not RE_URL.match(valor):
                errores[nombre] = "Escribe una dirección completa, empezando por https://"
            elif tipo == "email" and valor and not RE_EMAIL.match(valor):
                errores[nombre] = "El email no parece válido."
            elif tipo == "fecha" and valor and not RE_FECHA.match(valor):
                errores[nombre] = "Usa el formato AAAA-MM-DD."
            elif tipo == "nivel":
                if valor not in ("1", "2", "3", "4", "5"):
                    errores[nombre] = "Elige un nivel del 1 al 5."
                else:
                    valor = int(valor)
            elif tipo == "opcion" and valor not in [v for v, _ in op["opciones"]]:
                errores[nombre] = "Elige una de las opciones."
            valores[nombre] = valor
        return valores, errores

    # ============================================================ web pública
    @app.route("/")
    def inicio():
        db = get_db()
        proyectos = db.execute(
            "SELECT * FROM proyectos WHERE visible = 1"
            " ORDER BY destacado DESC, fecha DESC, id DESC").fetchall()
        habilidades = {}
        for h in db.execute("SELECT * FROM habilidades ORDER BY id"):
            habilidades.setdefault(h["categoria"], []).append(h)
        return render_template(
            "inicio.html",
            perfil=db.execute("SELECT * FROM perfil WHERE id = 1").fetchone(),
            proyectos=[p for p in proyectos if p["categoria"] == "informatica"],
            proyectos_hw=[p for p in proyectos if p["categoria"] != "informatica"],
            habilidades=habilidades,
            formacion=db.execute(
                "SELECT * FROM formacion ORDER BY fecha_inicio DESC, id").fetchall(),
            logros=db.execute(
                "SELECT * FROM logros ORDER BY categoria DESC, fecha DESC, id").fetchall(),
            form=session.pop("contacto_form", {}),
            errores=session.pop("contacto_errores", {}))

    @app.route("/proyectos/<int:id>")
    def proyecto(id):
        db = get_db()
        p = db.execute(
            "SELECT * FROM proyectos WHERE id = ? AND visible = 1", (id,)).fetchone()
        if p is None:
            abort(404)
        return render_template(
            "proyecto.html", p=p,
            perfil=db.execute("SELECT * FROM perfil WHERE id = 1").fetchone())

    @app.route("/contacto", methods=["POST"])
    def contacto():
        if request.form.get("web"):          # trampa para bots: campo invisible
            return redirect(url_for("inicio") + "#contacto")
        form = {k: request.form.get(k, "").strip() for k in ("nombre", "email", "mensaje")}
        errores = {}
        if not form["nombre"] or len(form["nombre"]) > 100:
            errores["nombre"] = "Dime cómo te llamas."
        if not RE_EMAIL.match(form["email"]) or len(form["email"]) > 200:
            errores["email"] = "Necesito un email válido para poder responderte."
        if not form["mensaje"]:
            errores["mensaje"] = "Escribe tu mensaje."
        elif len(form["mensaje"]) > 5000:
            errores["mensaje"] = "El mensaje es demasiado largo (máximo 5000 caracteres)."
        ip = "contacto:" + (request.remote_addr or "?")
        if not errores and demasiadas(ip, 5, 3600):
            errores["mensaje"] = "Has enviado varios mensajes seguidos. Inténtalo más tarde."
        if errores:
            session["contacto_form"], session["contacto_errores"] = form, errores
        else:
            apuntar(ip)
            db = get_db()
            db.execute(
                "INSERT INTO mensajes_contacto (nombre, email, mensaje) VALUES (?, ?, ?)",
                (form["nombre"], form["email"], form["mensaje"]))
            db.commit()
            flash("Mensaje enviado. Te responderé lo antes posible.", "ok")
        return redirect(url_for("inicio") + "#contacto")

    @app.route("/calculadora/")
    def calculadora():
        return send_from_directory(os.path.join(app.static_folder, "calculadora"), "index.html")

    @app.route("/media/<path:nombre>")
    def archivo(nombre):
        return send_from_directory(app.config["UPLOADS"], nombre)

    # ================================================================== admin
    @app.route("/admin/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            ip = "login:" + (request.remote_addr or "?")
            if demasiadas(ip, 5, 300):
                error = "Demasiados intentos. Espera cinco minutos."
            else:
                usuario = request.form.get("usuario", "").strip()
                clave = request.form.get("clave", "").encode("utf-8")[:72]
                db = get_db()
                fila = db.execute(
                    "SELECT * FROM usuarios_admin WHERE usuario = ?", (usuario,)).fetchone()
                # Se comprueba siempre un hash para no delatar si el usuario existe.
                guardado = fila["password_hash"].encode() if fila else HASH_FALSO
                if bcrypt.checkpw(clave, guardado) and fila:
                    intentos.pop(ip, None)
                    session.clear()
                    session["admin_id"] = fila["id"]
                    session["sello"] = sello(fila["password_hash"])
                    session["acceso_anterior"] = fila["ultimo_acceso"]
                    db.execute(
                        "UPDATE usuarios_admin SET ultimo_acceso = datetime('now')"
                        " WHERE id = ?", (fila["id"],))
                    db.commit()
                    destino = request.args.get("siguiente", "")
                    if not destino.startswith("/admin") or "//" in destino or "\\" in destino:
                        destino = url_for("admin")
                    return redirect(destino)
                apuntar(ip)
                error = "Usuario o contraseña incorrectos."
        return render_template("admin/login.html", error=error)

    @app.route("/admin/salir", methods=["POST"])
    def salir():
        session.clear()
        return redirect(url_for("inicio"))

    @app.route("/admin/")
    @login_requerido
    def admin():
        db = get_db()
        cuentas = {n: db.execute("SELECT COUNT(*) FROM %s" % n).fetchone()[0]
                   for n in ENTIDADES}
        recientes = db.execute(
            "SELECT * FROM mensajes_contacto ORDER BY leido, fecha DESC LIMIT 5").fetchall()
        return render_template("admin/panel.html", cuentas=cuentas, recientes=recientes)

    @app.route("/admin/perfil", methods=["GET", "POST"])
    @login_requerido
    def admin_perfil():
        db = get_db()
        actual = db.execute("SELECT * FROM perfil WHERE id = 1").fetchone()
        valores, errores = dict(actual), {}
        if request.method == "POST":
            valores, errores = leer_formulario(CAMPOS_PERFIL, actual)
            if not errores:
                columnas = ", ".join("%s = ?" % c for c in valores)
                db.execute("UPDATE perfil SET %s WHERE id = 1" % columnas,
                           list(valores.values()))
                db.commit()
                limpiar_subidas(CAMPOS_PERFIL, actual, valores)
                flash("Perfil guardado.", "ok")
                return redirect(url_for("admin_perfil"))
        return render_template(
            "admin/formulario.html", titulo="Perfil", campos=CAMPOS_PERFIL,
            valores=valores, errores=errores, volver=None)

    # --- CRUD genérico: el nombre de tabla solo se acepta si está en ENTIDADES
    def entidad_o_404(nombre):
        if nombre not in ENTIDADES:
            abort(404)
        return ENTIDADES[nombre]

    @app.route("/admin/<nombre>/")
    @login_requerido
    def admin_lista(nombre):
        ent = entidad_o_404(nombre)
        filas = get_db().execute(
            "SELECT * FROM %s ORDER BY %s" % (nombre, ent["orden"])).fetchall()
        etiquetas = {c[0]: c for c in ent["campos"]}
        return render_template("admin/lista.html", nombre=nombre, ent=ent,
                               filas=filas, etiquetas=etiquetas)

    @app.route("/admin/<nombre>/nuevo", methods=["GET", "POST"])
    @app.route("/admin/<nombre>/<int:id>", methods=["GET", "POST"])
    @login_requerido
    def admin_editar(nombre, id=None):
        ent = entidad_o_404(nombre)
        db = get_db()
        actual = None
        if id is not None:
            actual = db.execute("SELECT * FROM %s WHERE id = ?" % nombre, (id,)).fetchone()
            if actual is None:
                abort(404)
        errores = {}
        if request.method == "POST":
            valores, errores = leer_formulario(ent["campos"], actual)
            if not errores:
                cols = list(valores)
                if actual is None:
                    db.execute(
                        "INSERT INTO %s (%s) VALUES (%s)"
                        % (nombre, ", ".join(cols), ", ".join("?" * len(cols))),
                        list(valores.values()))
                else:
                    db.execute(
                        "UPDATE %s SET %s WHERE id = ?"
                        % (nombre, ", ".join("%s = ?" % c for c in cols)),
                        list(valores.values()) + [id])
                db.commit()
                if actual is not None:
                    limpiar_subidas(ent["campos"], actual, valores)
                flash("Guardado: %s." % ent["singular"], "ok")
                return redirect(url_for("admin_lista", nombre=nombre))
        elif actual is not None:
            valores = dict(actual)
        else:
            valores = {c[0]: c[3].get("defecto", "") for c in ent["campos"]}
        return render_template(
            "admin/formulario.html",
            titulo=("Editar " if actual else "Añadir ") + ent["singular"],
            campos=ent["campos"], valores=valores, errores=errores,
            volver=url_for("admin_lista", nombre=nombre),
            borrar=url_for("admin_borrar", nombre=nombre, id=id) if actual else None)

    @app.route("/admin/<nombre>/<int:id>/borrar", methods=["POST"])
    @login_requerido
    def admin_borrar(nombre, id):
        ent = entidad_o_404(nombre)
        db = get_db()
        fila = db.execute("SELECT * FROM %s WHERE id = ?" % nombre, (id,)).fetchone()
        if fila is None:
            abort(404)
        db.execute("DELETE FROM %s WHERE id = ?" % nombre, (id,))
        db.commit()
        limpiar_subidas(ent["campos"], fila)
        flash("Borrado: %s." % ent["singular"], "ok")
        return redirect(url_for("admin_lista", nombre=nombre))

    # --- Mensajes de contacto
    @app.route("/admin/mensajes/")
    @login_requerido
    def admin_mensajes():
        filas = get_db().execute(
            "SELECT * FROM mensajes_contacto ORDER BY fecha DESC, id DESC").fetchall()
        return render_template("admin/mensajes.html", filas=filas)

    @app.route("/admin/mensajes/<int:id>/<accion>", methods=["POST"])
    @login_requerido
    def admin_mensaje_accion(id, accion):
        db = get_db()
        if accion == "leido":
            db.execute("UPDATE mensajes_contacto SET leido = 1 WHERE id = ?", (id,))
        elif accion == "no-leido":
            db.execute("UPDATE mensajes_contacto SET leido = 0 WHERE id = ?", (id,))
        elif accion == "borrar":
            db.execute("DELETE FROM mensajes_contacto WHERE id = ?", (id,))
            flash("Mensaje borrado.", "ok")
        else:
            abort(404)
        db.commit()
        return redirect(url_for("admin_mensajes"))

    @app.route("/admin/cuenta", methods=["GET", "POST"])
    @login_requerido
    def admin_cuenta():
        error = None
        if request.method == "POST":
            db = get_db()
            fila = db.execute("SELECT * FROM usuarios_admin WHERE id = ?",
                              (g.admin["id"],)).fetchone()
            actual = request.form.get("actual", "").encode()[:72]
            nueva = request.form.get("nueva", "")
            if not bcrypt.checkpw(actual, fila["password_hash"].encode()):
                error = "La contraseña actual no es correcta."
            elif len(nueva) < 10:
                error = "La contraseña nueva debe tener al menos 10 caracteres."
            elif len(nueva.encode()) > 72:
                error = "La contraseña nueva es demasiado larga (máximo 72 bytes)."
            elif nueva != request.form.get("repetir", ""):
                error = "Las dos contraseñas nuevas no coinciden."
            else:
                nuevo_hash = hash_clave(nueva)
                db.execute("UPDATE usuarios_admin SET password_hash = ? WHERE id = ?",
                           (nuevo_hash, fila["id"]))
                db.commit()
                session["sello"] = sello(nuevo_hash)
                flash("Contraseña cambiada.", "ok")
                return redirect(url_for("admin_cuenta"))
        return render_template("admin/cuenta.html", error=error)

    @app.errorhandler(404)
    def no_encontrado(_e):
        return render_template("error.html", codigo=404,
                               mensaje="Esta página no existe."), 404

    @app.errorhandler(400)
    def mala_peticion(e):
        return render_template("error.html", codigo=400, mensaje=e.description), 400

    @app.errorhandler(413)
    def demasiado_grande(_e):
        return render_template("error.html", codigo=413,
                               mensaje="El archivo es demasiado grande (máximo 8 MB)."), 413

    # ------------------------------------------------------------------- CLI
    @app.cli.command("crear-admin")
    @click.option("--usuario", prompt="Usuario", default="admin")
    @click.password_option("--clave", prompt="Contraseña (mínimo 10 caracteres)")
    def crear_admin(usuario, clave):
        """Crea el administrador o le cambia la contraseña."""
        if len(clave) < 10 or len(clave.encode()) > 72:
            raise click.ClickException("La contraseña debe tener entre 10 y 72 caracteres.")
        db = get_db()
        db.execute(
            "INSERT INTO usuarios_admin (usuario, password_hash) VALUES (?, ?)"
            " ON CONFLICT(usuario) DO UPDATE SET password_hash = excluded.password_hash",
            (usuario, hash_clave(clave)))
        db.commit()
        click.echo("Administrador «%s» listo. Entra en /admin/" % usuario)

    return app


def sello(password_hash):
    """Huella de la contraseña vigente, guardada en la sesión."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def hash_clave(clave):
    return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt()).decode()


HASH_FALSO = bcrypt.hashpw(b"-", bcrypt.gensalt())


def _clave_secreta():
    """Clave para firmar las cookies de sesión; se genera una vez y se guarda."""
    ruta = os.path.join(INSTANCE, "secret_key")
    if not os.path.exists(ruta):
        descriptor = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as f:
            f.write(secrets.token_hex(32))
    with open(ruta) as f:
        return f.read().strip()


app = crear_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
