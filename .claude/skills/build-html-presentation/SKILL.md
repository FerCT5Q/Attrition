---
name: build-html-presentation
description: >-
  Crea, mejora o revisa presentaciones y decks HTML del proyecto Attrition
  (slides, diapositivas, deck, presentación ejecutiva o analítica, KPI slide)
  combinando la metodología de visualización de Julia (skill morgan-vis) con
  la plantilla y los patrones de html-slide-generator. Úsalo también para
  corregir o verificar un deck existente. No aplica a sitios web ni a
  PowerPoint.
---

# Presentaciones HTML con la metodología de Julia

Genera presentaciones en las que el mensaje, la evidencia y la elección visual
guíen la construcción. Tres capas, cada una con su responsabilidad:

| Capa | Fuente | Decide |
|---|---|---|
| Proyecto | [AGENTS.md](../../../AGENTS.md) | Privacidad, modo de entrega, cohortes, idioma, cifras, rutas |
| Criterio | [`morgan-vis`](../morgan-vis/SKILL.md) | Mensaje, gráfico, simplificación, amplificación, autocrítica |
| Motor | `html-slide-generator` | Plantilla, escenario, navegación, temas, layouts, implementación |

Este skill las coordina. Ante un conflicto, sigue
[precedencia y conflictos](references/precedencia-y-conflictos.md): la
declaración de «precedencia total» del generador sólo vale dentro de su
ámbito técnico.

## Dependencias

Resuelve los enlaces relativos desde el directorio de este `SKILL.md`.

- Lee completo `../morgan-vis/SKILL.md`. Es la versión operativa del
  [skill original de Julia](../../../docs/julia/SKILL.md), que se conserva
  intacto como fuente.
- Localiza `html-slide-generator`: primero en el catálogo de skills de la
  sesión; si no aparece, busca `html-slide-generator/SKILL.md` en
  `~/.agents/skills/`, `~/.codex/skills/` y `~/.claude/skills/`. Define
  `HTML_SKILL_ROOT` como la carpeta del `SKILL.md` que realmente leíste y lee
  ese archivo.
- Antes de construir o modificar HTML, lee
  [la integración técnica](references/html-integration.md) y las referencias
  del generador que correspondan al contenido.
- Si necesitas consultar Redshift, carga `attrition-redshift-db`; si evalúas
  una variable, también `evaluate-attrition-variable`. Presentar evidencia
  existente no implica reevaluar sus scores.

Si falta una dependencia, dilo, indica qué falta y completa sólo lo posible
(guion o revisión). No inventes una plantilla sustituta ni declares terminado
un HTML que no pudiste verificar.

## 1. Delimitar la presentación

Recupera de la petición y la conversación: audiencia, pregunta o decisión,
fuentes, periodo, alcance, tiempo disponible y archivo de salida. Pregunta
sólo por lo que cambie materialmente el resultado y no pueda inferirse.
Respeta el alcance de una revisión o corrección puntual.

Clasifica el entregable antes de consultar datos o renderizar:
`presentation` por defecto; `internal_analysis` sólo si el usuario lo declara
expresamente. Comprueba que las fuentes y agregados se puedan mostrar en ese
modo, incluidos los datos que quedarían embebidos en JavaScript.

Si el deck lo genera un script del proyecto (por ejemplo
`tools/build_distribution_html_v*.py` o
`tools/presentations/render_variable_assessment_v2.py`), cambia el script y
regenera una versión nueva; no edites a mano la salida ni sobrescribas una
versión anterior.

## 2. Aplicar los cuatro pasos de `morgan-vis`

Por cada mensaje candidato:

1. **Aclarar el mensaje:** qué se observa, contra qué se compara y por qué
   importa. Concentración, comparación y cambio sólo con evidencia pertinente;
   un cruce nuevo requiere primero una hipótesis específica.
2. **Elegir el gráfico:** cifra, gráfico, tabla o diagrama según el mensaje,
   antes de decidir CSS o Plotly.
3. **Simplificar:** etiquetas directas, escalas honestas, un foco visual.
4. **Amplificar:** título que afirme la conclusión respaldada, subtítulo con
   población, ventana y unidad, contexto y limitaciones que cambien la lectura.

Aplica las [extensiones de Attrition](../morgan-vis/references/extensiones-attrition.md)
a toda tasa o cohorte. No inventes cifras, fuentes, benchmarks ni
explicaciones causales para fortalecer un título.

## 3. Construir un único guion

Ordena los mensajes como historia vertical (del patrón general al detalle) u
horizontal (hallazgos paralelos comparables). Un gráfico, un mensaje; dos
gráficos comparten diapositiva sólo si se entienden juntos. No añadas
conclusiones ni secciones ajenas al encargo.

Presenta el guion así:

```text
Audiencia y decisión: …
Clasificación: presentation | internal_analysis
Salida propuesta: output/presentations/<fecha-hora>_<tema>/presentacion.html

| # | Mensaje (título) | Evidencia y fuente | Visual y layout |
|---|---|---|---|
| 1 | … | … | … |

Limitaciones que el deck mostrará: …
¿Procedo o ajustamos alcance, orden o visuales?
```

Esta es la **única puerta de planificación** y cumple §P del generador. Antes
de crear HTML espera la aprobación del guion, salvo aprobación previa aplicable
o instrucción de proceder de forma autónoma («adelante», «hazlo directamente»,
«sin pedirme confirmación», «go ahead»). La aprobación cubre el alcance
acordado; no pidas una segunda al pasar al generador. Una revisión sin
generación no activa la puerta.

A partir de cuatro diapositivas, propone una agenda como diapositiva 2; un
guion aprobado o una instrucción que prescinda de ella prevalece. No agregues
diapositivas fuera del alcance para cumplir patrones.

## 4. Construir

Copia la plantilla original y desarrolla el guion con el procedimiento de
[integración HTML](references/html-integration.md). En una presentación
existente, conserva su estructura útil y aplica sólo lo solicitado.

En este proyecto:

- Todo lo visible en español, incluidos controles de tema y navegación;
  `lang="es"`. Los identificadores técnicos pueden quedar en inglés.
- Enteros sin decimales y el resto con máximo un decimal en ejes, KPIs,
  tablas, etiquetas y tooltips. Los cálculos conservan su precisión.
- Sólo agregados permitidos; aplica supresión y cohortes antes de incrustar
  datos. Ocultar una fila en pantalla no la elimina del HTML.
- Al presentar evaluaciones de variables, respeta el flujo histórico y la
  explicación de cada validación exigidos por AGENTS.md; cita consulta,
  fecha, población y métricas.
- Verifica cifras contra las fuentes sin cambiar denominadores, periodos ni
  poblaciones. Una corrección visual no valida un score.

## 5. Verificar

1. **Estático:** ejecuta el verificador y corrige todos los errores; revisa
   los avisos.

   ```powershell
   & .venv\Scripts\python.exe -B `
     .agents\skills\build-html-presentation\scripts\verify_deck.py `
     '<deck.html>' --mode <presentation|internal_analysis>
   ```

   Comprueba plantilla, navegación, temas, `lang`, clasificación, recursos
   externos, imágenes no embebidas, contenido de ejemplo, claves sensibles y
   decimales visibles. No sustituye la revisión visual.
2. **Navegador:** con la herramienta disponible (por ejemplo Playwright),
   abre el deck a 1440×810, recorre todas las diapositivas en los cuatro
   temas y revisa recortes, superposiciones, legibilidad, gráficos ocultos
   inicialmente, navegación por teclado y errores de consola. Guarda las
   capturas en `tmp/` u `output/preview/`, nunca en la raíz del proyecto.
3. **Mensaje:** recorre el [checklist de Julia](../morgan-vis/references/checklist.md)
   sobre las capturas, y §22 del generador para el funcionamiento.

Corrige lo observado y repite las comprobaciones afectadas, sin reconstruir
toda la presentación por una corrección puntual.

## Entrega

Un HTML con CSS y JavaScript integrados. Si el usuario no indicó ruta, usa
`output/presentations/<fecha-hora>_<tema>/presentacion.html` sin sobrescribir
entregas anteriores. Auxiliares de construcción en `tools/`; entradas en sus
ubicaciones originales.

Devuelve el enlace al HTML y un resumen breve de lo comprobado y de las
limitaciones pendientes. Indica si necesita internet para Plotly. Si sólo
inspeccionaste el código, dilo: no declares revisión visual ni funcionamiento
comprobados. Guarda un guion o informe adicional sólo si el encargo lo pide.
