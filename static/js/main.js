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
  var enTransicion = false;

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

      function aplicar() {
        raiz.setAttribute('data-theme', nuevo);
        try { localStorage.setItem('tema', nuevo); } catch (e) { /* solo esta visita */ }
        pintarBoton();
        document.dispatchEvent(new Event('temacambiado'));
      }

      // Transición «simbionte» (ver style.css): una capa oscura recortada con
      // forma de mancha que sale del botón (a oscuro) o vuelve a él (a claro).
      var sinMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (sinMovimiento || enTransicion || !window.requestAnimationFrame) {
        aplicar();
        return;
      }
      enTransicion = true;
      var caja = boton.getBoundingClientRect();
      var x = caja.left + caja.width / 2, y = caja.top + caja.height / 2;
      var lejos = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
      // El núcleo de la mancha ocupa ~16 % del ancho del SVG a cada lado del
      // centro: con este tamaño final tapa hasta la esquina más lejana.
      var total = Math.ceil(lejos / 0.16);
      var aOscuro = nuevo === 'dark';
      var DURACION = 1150;
      var capa = document.createElement('div');
      capa.className = 'simbionte';
      capa.setAttribute('aria-hidden', 'true');

      function recortar(avance) {            // avance: 0 = nada, 1 = todo tapado
        var lado = total * avance;
        var tam = lado + 'px ' + lado + 'px';
        var pos = (x - lado / 2) + 'px ' + (y - lado / 2) + 'px';
        capa.style.webkitMaskSize = tam;
        capa.style.maskSize = tam;
        capa.style.webkitMaskPosition = pos;
        capa.style.maskPosition = pos;
      }

      function suave(t) {                    // arranca y frena despacio
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      }

      function terminar() {
        capa.remove();
        enTransicion = false;
      }

      // Al aclarar, la página ya está oscura: la capa la tapa entera, se
      // cambia el tema por debajo y la mancha se repliega.
      recortar(aOscuro ? 0 : 1);
      if (!aOscuro) capa.style.opacity = '0';
      document.body.appendChild(capa);
      if (aOscuro) {
        animar();
      } else {
        capa.getBoundingClientRect();        // fija el estado inicial del fundido
        capa.style.opacity = '1';
        setTimeout(function () { aplicar(); animar(); }, 300);
      }

      function animar() {
      var empieza = null;
      requestAnimationFrame(function paso(ahora) {
        if (empieza === null) empieza = ahora;
        var t = Math.min((ahora - empieza) / DURACION, 1);
        recortar(aOscuro ? suave(t) : 1 - suave(t));
        if (t < 1) {
          requestAnimationFrame(paso);
        } else if (aOscuro) {
          // Todo tapado: se cambia el tema y la capa se desvanece
          aplicar();
          capa.style.opacity = '0';
          setTimeout(terminar, 300);
        } else {
          terminar();
        }
      });
      }
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
     5. Amanecer de la portada
     Un canvas dibuja el horizonte de un planeta, la luz que sale por detrás
     y símbolos de física y de código que suben flotando. Se detiene cuando
     no se ve y, con «reducir movimiento», se queda en una imagen fija.
     ------------------------------------------------------------------------ */
  var lienzo = document.querySelector('.amanecer');
  if (lienzo && lienzo.getContext) {
    (function () {
      var ctx = lienzo.getContext('2d');
      var hueco = document.querySelector('.horizonte');
      var SIMBOLOS = ['λ', 'ħ', '∇', 'Σ', 'Δ', 'π', 'ψ', 'Ω', 'μ', '∫', '{}', '()', '[]',
        '<>', '//', '&&', '!=', '==', '01', '10', '0x', '::', '+', '*', '=', ';'];
      var ESPECTRO = ['107,28,255', '45,91,255', '25,195,255', '45,224,138',
        '232,232,58', '255,154,46', '255,61,61'];
      var quieto = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var ancho = 0, alto = 0, cima = 0, radio = 0, particulas = [];
      var inicio = null, anterior = 0, visible = true, pedido = null;
      var CIELO = '#08090a';    // el cielo es siempre de noche, también en modo claro
      var colorFondo = CIELO;
      var raton = { x: 0, y: 0, dentro: false };
      var RADIO_EMPUJE = 120;   // px alrededor del puntero

      function azar(a, b) { return a + Math.random() * (b - a); }

      // Altura del horizonte (la curva del planeta) en la columna x
      function horizonteEn(x) {
        var dx = x - ancho / 2;
        return cima + radio - Math.sqrt(Math.max(radio * radio - dx * dx, 0));
      }

      function nueva(alNacer) {
        var x = azar(0, ancho);
        var suelo = horizonteEn(x);
        return {
          x: x,
          y: alNacer ? suelo - azar(0, 30) : azar(0, suelo),
          vx: azar(-3, 3),
          vy: azar(-16, -5),
          talla: azar(9, 14),
          brillo: azar(0.25, 0.9),
          fase: azar(0, 6.28),
          ex: 0,            // empujón del ratón, que se va frenando
          ey: 0,
          edad: alNacer ? 0 : 5,
          signo: SIMBOLOS[Math.floor(Math.random() * SIMBOLOS.length)]
        };
      }

      function leerTema() {
        colorFondo = getComputedStyle(raiz).getPropertyValue('--fondo').trim() || '#08090a';
      }

      function medir() {
        var caja = lienzo.getBoundingClientRect();
        var escala = Math.min(window.devicePixelRatio || 1, 2);
        ancho = caja.width;
        alto = caja.height;
        lienzo.width = Math.round(ancho * escala);
        lienzo.height = Math.round(alto * escala);
        ctx.setTransform(escala, 0, 0, escala, 0, 0);
        var reserva = hueco ? hueco.offsetHeight : 160;
        cima = alto - reserva * 0.55;
        // Radio suficiente para que la curva llegue a los bordes sin salirse
        // del canvas (si no, el cielo quedaría cortado en recto por abajo)
        var caida = reserva * 0.5;
        radio = Math.max((ancho * ancho / 4 + caida * caida) / (2 * caida), ancho * 1.15, 900);
        var cuantas = Math.max(80, Math.min(320, Math.round(ancho * alto / 3600)));
        particulas = [];
        for (var i = 0; i < cuantas; i++) particulas.push(nueva(false));
      }

      function pintar(ahora) {
        pedido = null;
        if (inicio === null) { inicio = ahora; anterior = ahora; }
        var dt = Math.min((ahora - anterior) / 1000, 0.05);
        anterior = ahora;
        var t = (ahora - inicio) / 1000;
        // La luz sale en unos 2,6 s y después «respira» despacio
        var sale = quieto ? 1 : 1 - Math.pow(1 - Math.min(t / 2.6, 1), 3);
        var pulso = quieto ? 1 : 0.94 + 0.06 * Math.sin(t * 0.7);
        var cx = ancho / 2;

        ctx.fillStyle = CIELO;
        ctx.fillRect(0, 0, ancho, alto);

        // 1. Resplandor del amanecer (elipse achatada tras el horizonte)
        var alcance = Math.min(ancho * 0.42, 460) * (0.35 + 0.65 * sale) * pulso;
        var fuerza = sale;
        ctx.save();
        ctx.translate(cx, cima + 6);
        ctx.scale(1, 0.62);
        var luz = ctx.createRadialGradient(0, 0, 0, 0, 0, alcance);
        luz.addColorStop(0, 'rgba(255,238,220,' + 0.95 * fuerza + ')');
        luz.addColorStop(0.18, 'rgba(255,186,128,' + 0.6 * fuerza + ')');
        luz.addColorStop(0.5, 'rgba(255,122,64,' + 0.16 * fuerza + ')');
        luz.addColorStop(1, 'rgba(255,122,64,0)');
        ctx.fillStyle = luz;
        ctx.beginPath();
        ctx.arc(0, 0, alcance, 0, 6.2832);
        ctx.fill();
        ctx.restore();

        // 2. Símbolos que suben; brillan más cerca de la luz
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        for (var i = 0; i < particulas.length; i++) {
          var p = particulas[i];
          if (!quieto) {
            // El puntero aparta los símbolos cercanos; el empujón se amortigua
            if (raton.dentro) {
              var ex = p.x - raton.x, ey = p.y - raton.y;
              var lejos = Math.hypot(ex, ey);
              if (lejos < RADIO_EMPUJE) {
                var empuje = Math.pow(1 - lejos / RADIO_EMPUJE, 2) * 1400 * dt;
                lejos = lejos || 1;
                p.ex += ex / lejos * empuje;
                p.ey += ey / lejos * empuje;
              }
            }
            var freno = Math.exp(-2.2 * dt);
            p.ex *= freno;
            p.ey *= freno;
            p.x += (p.vx + p.ex) * dt;
            p.y += (p.vy + p.ey) * dt;
            p.edad += dt;
            if (p.y < -20 || p.x < -20 || p.x > ancho + 20) {
              particulas[i] = p = nueva(true);
            }
          }
          var suelo = horizonteEn(p.x);
          if (p.y > suelo - 4) continue;
          var altura = Math.max(p.y, 0) / suelo;                 // 0 arriba, 1 en el horizonte
          var cerca = Math.max(0, 1 - Math.hypot(p.x - cx, (p.y - cima) * 1.4) / (alcance * 1.5));
          var alfa = p.brillo * (0.12 + 0.88 * Math.pow(altura, 1.6))
            * Math.min(p.edad / 1.2, 1)
            * (0.75 + 0.25 * Math.sin(t * 1.3 + p.fase))
            * (0.35 + 0.65 * sale);
          alfa = Math.min(alfa * (0.9 + cerca * 0.9), 0.9);
          if (alfa < 0.02) continue;
          var tono = Math.round(170 + 85 * cerca) + ',' + Math.round(175 + 45 * cerca)
            + ',' + Math.round(190 - 20 * cerca);
          ctx.font = p.talla + 'px "JetBrains Mono", ui-monospace, monospace';
          ctx.fillStyle = 'rgba(' + tono + ',' + alfa + ')';
          ctx.fillText(p.signo, p.x, p.y);
        }

        // 3. El planeta: tapa lo que queda por debajo del horizonte. Se pinta
        //    del color de fondo de la página, así que en modo claro el planeta
        //    que asoma es la propia página.
        ctx.beginPath();
        ctx.arc(cx, cima + radio, radio, 0, 6.2832);
        ctx.fillStyle = colorFondo;
        ctx.fill();

        // 4. El borde iluminado, con los colores del espectro visible
        var borde = ctx.createLinearGradient(cx - ancho * 0.5, 0, cx + ancho * 0.5, 0);
        for (var c = 0; c < ESPECTRO.length; c++) {
          var pos = c / (ESPECTRO.length - 1);
          var centro = 1 - Math.abs(pos - 0.5) * 1.5;            // se apaga hacia los lados
          borde.addColorStop(pos, 'rgba(' + ESPECTRO[c] + ',' + Math.max(centro, 0.12) * sale + ')');
        }
        ctx.strokeStyle = borde;
        ctx.beginPath();
        ctx.arc(cx, cima + radio, radio, 0, 6.2832);
        ctx.globalAlpha = 0.22;
        ctx.lineWidth = 7;
        ctx.stroke();
        ctx.globalAlpha = 1;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        if (!quieto && visible && !document.hidden) pedir();
      }

      function pedir() {
        if (pedido === null) pedido = requestAnimationFrame(pintar);
      }

      lienzo.parentElement.classList.add('noche');   // texto claro sobre el cielo
      leerTema();
      medir();
      pedir();

      if ('ResizeObserver' in window) {
        new ResizeObserver(function () { medir(); pedir(); }).observe(lienzo);
      } else {
        window.addEventListener('resize', function () { medir(); pedir(); });
      }
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entradas) {
          visible = entradas[0].isIntersecting;
          if (visible) { anterior = performance.now(); pedir(); }
        }).observe(lienzo);
      }
      document.addEventListener('visibilitychange', function () {
        if (!document.hidden) { anterior = performance.now(); pedir(); }
      });
      // Posición del puntero respecto al canvas (el canvas no recibe eventos
      // porque está detrás del texto, así que se escucha en la ventana)
      window.addEventListener('pointermove', function (e) {
        var caja = lienzo.getBoundingClientRect();
        raton.x = e.clientX - caja.left;
        raton.y = e.clientY - caja.top;
        raton.dentro = raton.y > -RADIO_EMPUJE && raton.y < caja.height + RADIO_EMPUJE;
      }, { passive: true });
      raiz.addEventListener('mouseleave', function () { raton.dentro = false; });
      window.addEventListener('pointerup', function (e) {
        if (e.pointerType !== 'mouse') raton.dentro = false;   // al levantar el dedo
      });
      window.addEventListener('pointercancel', function () { raton.dentro = false; });

      // Al cambiar de tema, los colores del canvas se vuelven a leer
      document.addEventListener('temacambiado', function () { leerTema(); pedir(); });
      sistemaOscuro.addEventListener('change', function () { leerTema(); pedir(); });
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(pedir);
    })();
  }

  /* ------------------------------------------------------------------------
     6. Panel de administración: confirmar antes de borrar
     ------------------------------------------------------------------------ */
  document.addEventListener('submit', function (e) {
    var texto = e.target.getAttribute('data-confirmar');
    if (texto && !window.confirm(texto)) e.preventDefault();
  });
})();
