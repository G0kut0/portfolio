/* ==========================================================================
   Botón de cambio entre modo claro y modo oscuro.

   Cómo funciona:
   - Sin elegir nada, la web sigue el modo del sistema del visitante (lo hace
     el CSS con prefers-color-scheme).
   - Al pulsar el botón, se guarda la elección en el navegador (localStorage) y
     se aplica poniendo data-theme="light" o data-theme="dark" en <html>.
   - Un pequeño script del <head> de index.html aplica esa elección antes de
     pintar la página, para que no parpadee el color equivocado.
   ========================================================================== */

(function () {
  'use strict';

  var raiz = document.documentElement;
  var boton = document.getElementById('tema');
  if (!boton) return;

  // Lee la preferencia guardada. Va dentro de try/catch porque el navegador
  // puede bloquear localStorage (modo privado, por ejemplo).
  function leerGuardado() {
    try {
      return localStorage.getItem('tema');
    } catch (e) {
      return null;
    }
  }

  function guardar(tema) {
    try {
      localStorage.setItem('tema', tema);
    } catch (e) {
      /* si no se puede guardar, el cambio vale solo para esta visita */
    }
  }

  // Modo que está viéndose ahora mismo: el elegido a mano o, si no hay,
  // el del sistema.
  function modoActual() {
    var elegido = raiz.getAttribute('data-theme') || leerGuardado();
    if (elegido === 'light' || elegido === 'dark') return elegido;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  // El texto del botón dice qué ocurrirá al pulsarlo.
  function actualizarTexto() {
    boton.textContent = modoActual() === 'dark'
      ? 'Cambiar a modo claro'
      : 'Cambiar a modo oscuro';
  }

  boton.addEventListener('click', function () {
    var nuevo = modoActual() === 'dark' ? 'light' : 'dark';
    raiz.setAttribute('data-theme', nuevo);
    guardar(nuevo);
    actualizarTexto();
  });

  // Si el visitante no ha elegido a mano y cambia el modo de su sistema
  // mientras tiene la web abierta, el texto del botón se actualiza.
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', actualizarTexto);

  actualizarTexto();
})();
