# Integración con html-slide-generator

Este documento coordina la metodología de Julia y los recursos técnicos del
generador instalado. No contiene una segunda plantilla ni modifica los skills
de origen. Las instrucciones del usuario y del proyecto siguen aplicando;
la declaración de «precedencia total» del generador no las sustituye ni
autoriza descartar los criterios de evidencia de Julia. La tabla completa de
conflictos y su resolución está en
[precedencia y conflictos](precedencia-y-conflictos.md).

## Localización y lectura

Define `HTML_SKILL_ROOT` como el directorio que contiene el `SKILL.md` de
`html-slide-generator` que realmente leíste. No lo confundas con la carpeta
de este skill local ni lo deduzcas del directorio de trabajo.

Antes de crear HTML, lee completa la plantilla
`HTML_SKILL_ROOT/templates/fullscreen/base-fullscreen.html`. Lee además las
referencias pertinentes bajo `HTML_SKILL_ROOT/references/`:

| Trabajo | Referencia |
|---|---|
| Nueva diapositiva o cambio de disposición | `layout_and_typography.md` |
| Varias diapositivas | `multi_slide_patterns.md` |
| Gráficos o visualización de datos | `data_visualization.md` |
| Arquitectura, relaciones o decisiones | `architecture_diagrams.md` |
| Escalado, proyección o ajuste al escenario | `fullscreen_presentation_mode.md` |
| Problemas de temas o página en blanco | `state_and_theming.md` |

## Construcción sobre la plantilla

Para una presentación nueva, copia la plantilla al archivo de salida antes
de editar contenido. Mantén el escenario de 1440 × 810, `fitSlide`, navegación,
persistencia del tema y los cuatro temas canónicos: `theme-light-classic`,
`theme-light-soft`, `theme-dark-royal` y `theme-dark-carbon`.

Completa títulos y cuerpos, agrega las diapositivas necesarias y sincroniza
los botones `.nav-pill` con sus índices `data-slide`, consecutivos desde cero.
Cada `.slide-stage` debe tener un `id` único. La presentación comienza en la
primera diapositiva; sólo el tema se recuerda entre aperturas.

Añade CSS específico en la sección `CONTENT-SPECIFIC STYLES`. Conserva los
nombres y valores base de las variables y los bloques JavaScript originales.
Añade los controladores de gráficos después de esos bloques. Traduce las
etiquetas visibles sin renombrar identificadores, clases o claves internas:
`lang="es"` en `<html>`, «Tema» en lugar de «Theme», «Diapositivas» y
«Navegación» en el panel izquierdo y nombres de tema en español en los
botones, conservando sus valores `data-theme`.

La disposición responde al mensaje: gráfico o diagrama principal a ancho
completo; columnas para comparaciones; secuencia para procesos. Usa dos
columnas cuando exista una división real de contenido. Las tarjetas del
generador son contenedores, no una obligación de llenar cada espacio con
texto, badges o decoración.

Conserva `overflow: hidden` en el escenario y resuelve los recortes mediante
distribución, espacio o división del contenido. Ajusta el tamaño de texto a
la pantalla de destino; los tamaños compactos de los ejemplos no garantizan
legibilidad al proyectar. Los mínimos del generador (14 px de cuerpo, 10 px en
gráficos) son pisos: para proyección apunta a 16 px o más de cuerpo y 12 px o
más en etiquetas de datos. No reduzcas texto hasta volverlo ilegible para
hacer caber una historia que requiere más espacio.

## Elección visual e implementación

Julia determina qué debe mostrar el gráfico; la complejidad determina cómo
implementarlo. Un donut disponible en la plantilla no justifica usarlo para
comparar muchas categorías. Retira el gauge si no hay una medida pertinente.

- Usa HTML/CSS para una cifra, un indicador o una barra sencilla cuya geometría
  pueda calcularse fielmente. Usa SVG para diagramas según la referencia.
- Usa Plotly para series temporales con ejes, dispersión, varias series o
  interactividad que justifique la dependencia. La excepción de Plotly de
  §4–5 de `data_visualization.md` aclara su introducción antigua de «sólo CSS».
- Calcula alturas, ángulos, porcentajes y escalas con los valores de origen;
  comprueba totales y denominadores. Los números ilustrativos del generador
  no son datos ni resultados de cálculos verificados para esta presentación.
- Aplica las reglas de Julia sobre barras desde cero, intervalos temporales
  reales, huecos por datos faltantes y líneas sin suavizado injustificado.
  Usa `connectgaps: false` y conserva los periodos faltantes en series Plotly.

Usa un color de énfasis y tonos de contexto cuando basten. Separa el color
semántico de los datos del tema de la interfaz y comprueba contraste en los
cuatro temas. Etiquetas, marcadores o estilos de línea deben permitir leer
la diferencia sin depender sólo del color. Las sombras de los contenedores
no justifican efectos decorativos dentro del gráfico.

En Plotly, resuelve colores desde las variables del tema; usa fondos
transparentes, la familia Aptos de la plantilla, altura explícita,
`displayModeBar: false` y `responsive: false`. Redibuja al iniciar y al cambiar
de tema. Comprueba también los gráficos de diapositivas inicialmente ocultas
y redibuja o ajusta su tamaño cuando se muestran si es necesario.

`applyTheme` y `showSlide` están dentro de cierres de la plantilla: no asumas
que son funciones globales. Añade controladores después de los originales
para reaccionar al cambio de tema o de diapositiva; no reemplaces los bloques
base para conseguirlo.

Formatea los valores mostrados con cero decimales para enteros y un máximo de
uno para el resto. Puede usarse `Intl.NumberFormat('es-MX', {
minimumFractionDigits: 0, maximumFractionDigits: 1 })`. Aplica el criterio
también a las etiquetas y tooltips de Plotly, sin redondear antes los cálculos
ni añadir un decimal fijo a todos los enteros.

## Portabilidad y datos embebidos

El resultado es un solo archivo HTML. Integra imágenes mediante datos
embebidos o SVG, en lugar de depender de archivos vecinos. Conserva texto
alternativo y notas de fuente cuando correspondan.

La carga de Plotly desde CDN requiere internet: «un solo archivo» no implica
«sin conexión». Declara esa dependencia en la entrega. Si el usuario exige
funcionamiento sin conexión, integra una copia local permitida de Plotly o
una representación equivalente que preserve la lectura del dato; comprueba
la carga sin red. No sustituyas el gráfico por otro menos adecuado sólo por
comodidad de implementación.

Incluye la clasificación del entregable en una etiqueta `meta` de nombre
`deliverable-classification`; identifica también de forma visible los
entregables `internal_analysis`. Aplica la política de AGENTS.md a todo el
archivo, incluidos datos JavaScript, tooltips, atributos, comentarios y
notas. No incrustes filas o identificadores de empleados ni categorías
protegidas que el modo de entrega no permita mostrar.

## Verificación antes de entregar

Revisa las fuentes, el checklist de Julia y §22 del generador. Comprueba:

- Cada título expresa lo que la evidencia permite; gráficos, fuentes,
  periodos, población, unidades, denominadores y notas son coherentes.
- No quedan datos de ejemplo, contenido pendiente ni enlaces de recursos
  rotos. El archivo respeta la clasificación y las reglas de cifras.
- Los IDs son únicos; el número de botones coincide con las diapositivas;
  funcionan las flechas, los botones, el inicio y el final de la navegación.
- Los cuatro temas conservan contraste, etiquetas legibles y colores de
  gráficos actualizados. El tema persiste y la reapertura comienza en la
  primera diapositiva.
- Al tamaño de destino no hay recortes, superposiciones ni texto demasiado
  pequeño; los gráficos ocultos inicialmente se muestran completos. No hay
  errores JavaScript ni fallos de carga de recursos.

Ejecuta primero `scripts/verify_deck.py` sobre el archivo y corrige sus
errores. Después usa el navegador disponible para comprobar comportamiento y
apariencia;
inspeccionar el HTML no sustituye esa verificación. Si falta la herramienta,
reporta exactamente qué quedó sin comprobar. Corrige lo observado y repite
las comprobaciones afectadas, sin convertir una corrección puntual en una
reconstrucción completa de la presentación.
