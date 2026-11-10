# Design Map

Fuente: https://linear.app (una página, capturada a 1440×900).

## Spacing Scale
- 4px, 6px, 8px, 12px, 16px, 24px, 32px, 128px · unidad base 4px · secciones con 128px arriba y abajo

## Font Hierarchy
- hero: 64px / peso 510 / Inter Variable / tracking -1.408px
- h2: 48px / peso 510 / Inter Variable / tracking -1.056px
- lead: 18px / peso 400 / Inter Variable
- body: 15px / peso 400 / Inter Variable / tracking -0.165px
- ui: 13px / peso 510 / Inter Variable
- label: 12px / peso 510 / Inter Variable
- code: 14px / peso 400 / Berkeley Mono

## Color Palette
- background: #08090A
- panel: #0F1011
- surface-overlay: rgba(255,255,255,0.02-0.05)
- text-primary: #F7F8F8
- text-secondary: #D0D6E0
- text-tertiary: #8A8F98
- text-quaternary: #62666D
- border: rgba(255,255,255,0.08)
- button-primary: #E5E5E6
- accent-focus: #5E6AD2

## Image Ratios
- Sin fotografías: capturas de producto dentro de paneles con borde.

## Component Tokens
- Radios: 4px, 8px, 12px, 16px, 9999px
- Sombras: 0 0 0 1px rgba(0,0,0,0.2) · inset 0 0 0 0.5px rgba(255,255,255,0.08) · 0 2px 32px rgba(0,0,0,0.25)
- Botón principal: píldora #E5E5E6 con texto #08090A, 13px peso 510, alto 32px (44px en CTA)
- Movimiento: hover color 0.1s cubic-bezier(0.25,0.46,0.45,0.94); texto que pasa de desenfocado a nítido al cargar; rejilla de puntos en bucle de 2.8 s
- Ancho máximo: 1436px

---

# Taste DNA

### Jerarquía por luminosidad, no por color
- **Trigger**: Al separar título, cuerpo, apoyo y metadatos sobre fondo casi negro
- **Decision**: Eligió cuatro grises escalonados (#F7F8F8, #D0D6E0, #8A8F98, #62666D) en lugar de colores de marca por nivel
- **Reason**: En un fondo #08090A el ojo ordena por brillo antes que por tono; el color queda libre para significar estado
- **Evidence**: #8A8F98 en 180 nodos de texto; #62666D en 131; el índigo #5E6AD2 solo aparece en el enlace de foco

### Bordes de medio píxel en vez de sombras
- **Trigger**: Al delimitar tarjetas y paneles en oscuro
- **Decision**: Eligió líneas de 0.5px rgba(255,255,255,0.08) y rellenos blancos al 2-5 % en lugar de sombras de elevación
- **Reason**: Una sombra negra sobre negro no se ve; un borde claro muy fino dibuja el contorno sin añadir peso
- **Evidence**: 54 elementos con borde 0.5px al 8 %; la sombra más usada es un anillo de 1px; rellenos rgba(255,255,255,0.02) y 0.04

### Peso 510 y tracking negativo
- **Trigger**: Al componer titulares grandes con Inter
- **Decision**: Eligió peso 510 con interlineado 1.0 y tracking -0.022em en lugar de negrita 700
- **Reason**: A 64px la negrita emborrona las contraformas; un peso intermedio apretado mantiene el titular denso y legible
- **Evidence**: h1 64px/64px peso 510 tracking -1.408px; h2 48px/48px peso 510 tracking -1.056px; ningún texto por encima de 510

### Movimiento corto en la interfaz, lento en el ambiente
- **Trigger**: Al decidir qué se anima
- **Decision**: Eligió transiciones de 0.1-0.16 s para hover y una única entrada desenfocada en lugar de animaciones de scroll llamativas en cada bloque
- **Reason**: La respuesta inmediata transmite velocidad; lo decorativo se reserva a bucles lentos de fondo que no compiten con la lectura
- **Evidence**: color 0.1s en 187 elementos; curva cubic-bezier(0.25,0.46,0.45,0.94); bucles de fondo de 2.4-2.8 s
