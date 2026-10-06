# Precedencia y conflictos entre fuentes

`html-slide-generator` se declara con «precedencia total» y pide descartar
cualquier spec de diseño externa. En este proyecto esa declaración sólo
aplica dentro de su ámbito técnico. Orden de precedencia:

1. Instrucciones explícitas del usuario para el encargo.
2. [AGENTS.md](../../../../AGENTS.md): privacidad, modo de entrega, cohortes,
   idioma, formato de cifras, organización de archivos.
3. Este skill (`build-html-presentation`) y su integración.
4. `morgan-vis`: mensaje, elección del gráfico, simplificación, amplificación.
5. `html-slide-generator`: plantilla, escenario, navegación, temas, patrones
   de layout y de implementación.

Un nivel inferior sólo decide lo que el superior no regula. La plantilla del
generador sigue siendo obligatoria como punto de partida.

## Conflictos conocidos y resolución

| Tema | Generador dice | Se resuelve así |
|---|---|---|
| Precedencia y specs externas | Sobrescribe otras instrucciones; descarta specs de diseño | Aplica sólo a plantilla, temas y JS base. No descarta AGENTS.md, el mensaje de Julia ni la política de color de datos del proyecto. |
| Paletas | Prohíbe paletas propias | Los 4 temas de interfaz no cambian. El color semántico de datos (énfasis/gris, o `config/attrition_color_policy_*.json`) es independiente del tema y se define en `CONTENT-SPECIFIC STYLES` o en el código del gráfico. |
| Donut y leyendas | Donut con leyenda como patrón estándar | Sólo para una proporción del total con ≤5 porciones; preferir etiquetas directas. |
| Gauge | Presente en el encabezado de la plantilla | Retirarlo salvo que exista una medida actual-vs-meta pertinente. |
| Decoración | Sombras, bandas con gradiente, badges; «never pad with empty space» | Sombras de tarjeta permitidas como contenedor; nada decorativo dentro del gráfico. El espacio vacío se acepta cuando la alternativa es relleno sin mensaje. |
| Densidad mínima | Metas de contenido mínimo por layout | Prevalece «un gráfico, un mensaje». No agregues texto o badges para llenar. |
| CSS vs Plotly | `data_visualization.md` abre con «sólo CSS» y después permite Plotly | Vale la tabla de §4–5: Plotly para ejes, varias series, tiempo o interactividad justificada. |
| Tamaño de letra | Mínimos de 10–14 px | Son pisos, no objetivos. Para proyección usa texto de cuerpo ≥16 px y etiquetas de datos ≥12 px cuando quepa. |
| Idioma | `lang="en"`; etiquetas «Theme», «Slides», «Navigation» | `lang="es"`; traduce las etiquetas visibles («Tema», «Diapositivas», «Navegación») sin cambiar clases, IDs ni `data-theme`. |
| Cifras | Ejemplos con dos decimales | Enteros sin decimales; resto con máximo un decimal en todo lo visible. |
| Imágenes | Archivo en la misma carpeta del HTML | Un solo archivo: embebe como data URI o SVG. |
| Plotly CDN | «Sin dependencias de runtime» | Requiere internet; decláralo en la entrega. |
| Aprobación | Frases en inglés («go ahead») | Acepta equivalentes en español («adelante», «hazlo», «sin confirmar»). Una sola puerta de planificación. |
| Agenda | Obligatoria desde 4 diapositivas | Proponerla; una instrucción del usuario o guion aprobado sin agenda prevalece. |

## Qué no se negocia del generador

- Copiar `base-fullscreen.html`; no escribir el shell desde cero.
- Escenario 1440×810 con `overflow: hidden`, `fitSlide`, guardia de DPR.
- Los 4 nombres de tema, sus variables y la clave `slide-studio-theme`.
- Los dos bloques JavaScript base intactos; los controladores nuevos van
  después.
- Un `.nav-pill` por `.slide-stage`, índices `data-slide` consecutivos desde
  cero, IDs únicos.
- En Plotly: fondos transparentes, fuente Aptos, altura fija,
  `displayModeBar: false`, `responsive: false` y redibujo al cambiar tema.
