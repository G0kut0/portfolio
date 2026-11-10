/* ==========================================================================
   Portfolio de José Antonio — comportamiento de la interfaz.
   Todo es mejora progresiva: sin JavaScript la web se lee igual.
   ========================================================================== */
(function () {
  'use strict';

  var raiz = document.documentElement;

  /* ------------------------------------------------------------------------
     1. Modo claro / oscuro
     Sin elegir nada se sigue el modo del sistema. Al pulsar el botón, la
     elección se guarda en localStorage y se aplica con data-theme en <html>
     (un script del <head> la aplica antes de pintar para que no parpadee).
     ------------------------------------------------------------------------ */
  var boton = document.getElementById('tema');
  var sistemaOscuro = window.matchMedia('(prefers-color-scheme: dark)');

  function modoActual() {
    var elegido = raiz.getAttribute('data-theme');
    if (elegido === 'light' || elegido === 'dark') return elegido;
    return sistemaOscuro.matches ? 'dark' : 'light';
  }

  function pintarBoton() {
    if (!boton) return;
    var modo = modoActual();
    boton.dataset.modo = modo;
    boton.setAttribute('aria-label',
      modo === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
  }

  if (boton) {
    boton.addEventListener('click', function () {
      var nuevo = modoActual() === 'dark' ? 'light' : 'dark';
      raiz.setAttribute('data-theme', nuevo);
      try { localStorage.setItem('tema', nuevo); } catch (e) { /* solo esta visita */ }
      pintarBoton();
    });
    sistemaOscuro.addEventListener('change', pintarBoton);
    pintarBoton();
  }

  /* ------------------------------------------------------------------------
     2. Aparición al hacer scroll
     Los elementos con data-reveal empiezan desenfocados y se aclaran cuando
     entran en pantalla (el CSS hace la transición al añadir la clase "visto").
     ------------------------------------------------------------------------ */
  var revelables = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window) {
    var observador = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (entrada) {
        if (entrada.isIntersecting) {
          entrada.target.classList.add('visto');
          observador.unobserve(entrada.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revelables.forEach(function (el) { observador.observe(el); });
  } else {
    revelables.forEach(function (el) { el.classList.add('visto'); });
  }

  /* ------------------------------------------------------------------------
     3. Foco de luz que sigue al puntero en las tarjetas
     ------------------------------------------------------------------------ */
  document.querySelectorAll('.foco').forEach(function (tarjeta) {
    tarjeta.addEventListener('pointermove', function (e) {
      var caja = tarjeta.getBoundingClientRect();
      tarjeta.style.setProperty('--mx', (e.clientX - caja.left) + 'px');
      tarjeta.style.setProperty('--my', (e.clientY - caja.top) + 'px');
    });
  });

  /* ------------------------------------------------------------------------
     4. Menú: resalta la sección que se está leyendo
     ------------------------------------------------------------------------ */
  var enlaces = {};
  document.querySelectorAll('.barra nav a[href*="#"]').forEach(function (a) {
    enlaces[a.hash.slice(1)] = a;
  });
  var secciones = document.querySelectorAll('main section[id]');
  if (secciones.length && 'IntersectionObserver' in window) {
    var espia = new IntersectionObserver(function (entradas) {
      entradas.forEach(function (entrada) {
        if (!entrada.isIntersecting) return;
        Object.keys(enlaces).forEach(function (id) {
          enlaces[id].removeAttribute('aria-current');
        });
        var enlace = enlaces[entrada.target.id];
        if (enlace) enlace.setAttribute('aria-current', 'true');
      });
    }, { rootMargin: '-45% 0px -50% 0px' });
    secciones.forEach(function (s) { espia.observe(s); });
  }

  /* ------------------------------------------------------------------------
     5. Panel de administración: confirmar antes de borrar
     ------------------------------------------------------------------------ */
  document.addEventListener('submit', function (e) {
    var texto = e.target.getAttribute('data-confirmar');
    if (texto && !window.confirm(texto)) e.preventDefault();
  });
})();
