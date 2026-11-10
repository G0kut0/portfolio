# Portfolio de José Antonio

Web de portfolio con panel de administración propio (un pequeño CMS hecho desde cero).

- **Python**: Flask.
- **SQL**: SQLite, con las consultas escritas a mano (sin ORM). El esquema está en `schema.sql`.

## Puesta en marcha

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/flask --app app crear-admin      # elige usuario y contraseña
.venv/bin/flask --app app run
```

La web queda en http://127.0.0.1:5000 y el panel en http://127.0.0.1:5000/admin/.

La primera vez se crea la base de datos (`instance/portfolio.db`) con el contenido
inicial. A partir de ahí todo se edita desde el panel.

## Qué hay en cada sitio

| Archivo | Para qué sirve |
| --- | --- |
| `app.py` | Rutas de la web pública y del panel. La lista `ENTIDADES` define qué secciones y campos se editan. |
| `db.py` | Conexión a SQLite y contenido inicial. |
| `schema.sql` | Las 7 tablas: `perfil`, `proyectos`, `habilidades`, `formacion`, `logros`, `mensajes_contacto`, `usuarios_admin`. |
| `templates/` | Plantillas HTML (las del panel, en `templates/admin/`). |
| `static/` | CSS, JavaScript y la calculadora TLAP. |
| `uploads/` | Imágenes y PDF subidos desde el panel (no se guardan en git). |
| `instance/` | Base de datos y clave de sesión (no se guardan en git). |

## Seguridad

- Contraseñas con hash **bcrypt**; se registra la fecha del último acceso. Al cambiar
  la contraseña se cierran las demás sesiones abiertas.
- Protección CSRF en todos los formularios.
- Freno por IP: 5 intentos de acceso fallidos cada 5 minutos y 5 mensajes de contacto por hora.
- Cabeceras de seguridad en todas las respuestas (CSP, `X-Frame-Options`, `nosniff`).
- Las subidas solo admiten PNG, JPG, WEBP, GIF y PDF (máximo 8 MB), se guardan con nombre
  aleatorio y se borran del disco al sustituirlas o quitarlas.
- Ni la base de datos, ni la clave de sesión, ni las subidas se guardan en git.

## Publicarla en internet

`flask run` es solo para desarrollo. En un servidor, usa un servidor WSGI
(por ejemplo `gunicorn app:app`) detrás de HTTPS y define `COOKIES_SEGURAS=1`
para que la cookie de sesión solo viaje cifrada. No actives nunca el modo debug
(`--debug` o `FLASK_DEBUG=1`) en un servidor público: permite ejecutar código.
Si hay un proxy delante (nginx, etc.), configura `ProxyFix` de Werkzeug para que el
freno por IP vea la dirección real del visitante. Haz copia de `instance/` y `uploads/`.

## Diseño

La dirección visual (fondo casi negro, jerarquía por grises, bordes finos, Inter con
peso 510 y animaciones cortas) sale del análisis de linear.app guardado en
`docs/diseno/`. Lo propio de esta web es el haz con los colores del espectro visible.

Las animaciones están en `static/css/style.css` (sección 3) y `static/js/main.js`,
y se desactivan solas si el visitante tiene activado «reducir movimiento».
