# Plan detallado: presentación de la evolución de B a C + QVoice

## 1. Contexto del encargo

El usuario necesita presentar a líderes y Recursos Humanos los avances y resultados del trabajo sobre el modelo de attrition voluntaria de Engineering. La presentación debe explicar de dónde partimos, qué probamos, qué aprendimos y cómo llegamos al modelo elegido. El recorrido principal es **B → C → C + QVoice**, acompañado por las pruebas de B + QVoice, los ajustes de estimación, las nuevas combinaciones de encuesta y el experimento D.

La referencia visual es la presentación HTML de Julia del 5 de octubre de 2026, con el ajuste «Level / 8 groups». Esa presentación corresponde a una etapa anterior: explica B y todavía presenta QVoice y el bosque de supervivencia como trabajo pendiente. El nuevo relato debe actualizar ese estado con los experimentos ya terminados, conservando la extensión y el estilo de la referencia.

El usuario pidió **la misma cantidad de diapositivas que el ejemplo**, lenguaje sencillo y tablas, imágenes y animaciones que hagan comprensible la selección. Se comprobó que el archivo de ejemplo contiene **9 diapositivas, incluida la agenda**. El tiempo disponible es de 20 minutos; en la conversación se acordaron **18 minutos de exposición y 2 para preguntas**, diapositivas en **inglés** y audiencia principal de **líderes y Recursos Humanos**. El plan y las notas del presentador se redactarán en español.

La decisión vigente, confirmada el 10 de octubre de 2026, es **continuar con C + QVoice, identificado como CQ, sin calibración posterior adicional del riesgo a seis meses**. D no mostró una mejora estable que justificara sustituirlo. El objetivo de negocio es identificar grupos que concentran más salidas para orientar posibles acciones, con estimaciones útiles y grupos que puedan explicarse con claridad.

La elección corresponde a la etapa de selección de modelo. El piloto todavía no ha comenzado. Los resultados disponibles son históricos; la combinación final archivada en septiembre aún no tiene evaluación posterior a su ajuste. Estas precisiones forman parte del relato y deben aparecer de forma breve y comprensible.

Este documento reúne el contexto, las decisiones, las fuentes, el guion y las condiciones de implementación. Su finalidad es que otra persona pueda revisar o construir la presentación **sin necesitar la conversación anterior**. La petición actual es documentar el plan; la construcción del HTML es la etapa posterior descrita aquí.

### Datos del documento

| Campo | Valor |
|---|---|
| Fecha de elaboración | 10 de octubre de 2026 |
| Estado | Plan detallado para revisión e implementación |
| Clasificación de la futura presentación | `presentation` |
| Carpeta solicitada por el usuario | `C:\Dev\Python\Attrition\planes` |
| Archivo de este plan | `20261010-presentacion-evolucion-b-cq.md` |
| Fuente de la decisión actual | [model-selection-current.md](../docs/context/model-selection-current.md) |

## 2. Decisiones cerradas para la implementación

| Aspecto | Decisión |
|---|---|
| Cantidad | Exactamente 9 diapositivas; la agenda ocupa la posición 2 |
| Tiempo | 18 minutos de relato y 2 minutos para preguntas |
| Audiencia | Líderes y Recursos Humanos |
| Idioma visible | Inglés, incluidos títulos, tablas, notas breves y controles |
| Idioma del material de apoyo | Español para guion, explicación de evidencia y validación |
| Formato | Un HTML autónomo, panorámico, con escenario de 1440 × 810 |
| Identidad visual | Base vigente de Julia, tipografía Aptos y cuatro temas existentes |
| Modelo elegido | `engineering-c-qvoice-20261008-v1`, denominado CQ |
| Comparación central | Priorizar grupos que suman 30% de la población en cada foto mensual |
| Uso del 30% | Escenario de comparación; no representa un presupuesto operativo ya aprobado |
| Evidencia | Resultados agregados archivados; cada cifra tendrá una referencia verificable |
| Imágenes | Gráficos e ilustraciones explicativas integradas en el HTML |
| Animaciones | Tres secuencias breves, en las diapositivas 3, 6 y 7 |
| Interacción | Reproducción manual; navegación entre diapositivas mediante los controles existentes |
| Archivo final | `output/presentations/<YYYYMMDD-HHmm>_evolucion-b-cq/presentacion-eng.html` |

El resultado debe permitir que la audiencia responda cuatro preguntas: **qué teníamos con B, qué aportaron C y QVoice, por qué conservamos CQ después de D y qué falta comprobar antes del uso**.

## 3. Base visual y reglas del proyecto

### 3.1 Archivos de referencia

- Ejemplo indicado por el usuario: [presentación de Julia](../output/presentations/20261005-1044_seleccion-modelo-julia-8-groups/presentacion-eng.html).
- Registro de la base vigente: [model-selection-base.json](../config/presentations/model-selection-base.json).
- Copia de referencia: [base Julia con 8 grupos de nivel](../references/presentations/model-selection/20261005-julia-8-groups/presentacion-eng.html).
- Flujo de exportación: [README de presentaciones](../tools/presentations/README.md).

El ejemplo y la copia de referencia tienen el mismo SHA-256, comprobado al elaborar este documento:

```text
1dfc30dd99a6205ce067ed7a3abf4828748f1f09b736045ae2d6e5465b89a9ae
```

La implementación partirá de una copia de esa base. El exportador existente es `tools/presentations/build_model_selection_deck_v9.py`, que exporta la base vigente por defecto. La opción `--historical` reproduce una versión anterior y no corresponde a este encargo.

### 3.2 Instrucciones que debe leer quien implemente

1. [AGENTS.md](../AGENTS.md).
2. [build-html-presentation](../.agents/skills/build-html-presentation/SKILL.md), incluida su integración y precedencia.
3. [morgan-vis](../.agents/skills/morgan-vis/SKILL.md), sus extensiones de Attrition y su checklist.
4. El skill instalado `html-slide-generator`, su plantilla y las referencias de disposición, gráficos, múltiples diapositivas e interacción que corresponden al trabajo.

El inglés es una preferencia explícita confirmada por el usuario y coincide con la base vigente. Esta decisión prevalece sobre el idioma español genérico indicado para otros reportes del proyecto. El material explicativo de construcción permanece en español.

### 3.3 Alcance del trabajo posterior

La construcción consiste en presentar y verificar evidencia existente. No requiere entrenamiento, consultas nuevas a Redshift, cambios de scores de variables ni modificación de la elección de modelo. Si surgiera una necesidad de consulta nueva, sería un cambio de alcance que exige las reglas y skills de datos correspondientes.

La copia vigente de Julia y los resultados históricos se preservarán como entradas. La presentación nueva tendrá su propia carpeta. Este plan no actualiza el registro de la base vigente ni declara una nueva base oficial.

## 4. Mapa de los modelos y su papel en la historia

Esta sección es información para el implementador y el presentador. Las identificaciones técnicas no deben convertirse en una lista de tecnicismos en las diapositivas.

| Modelo o prueba | Qué significa | Papel en el relato |
|---|---|---|
| B | Modelo confirmado el 3 de octubre: ocho señales de RH y dos combinaciones, con estimación mensual acumulada a seis meses | Punto de partida y agrupaciones conocidas |
| B + QVoice | Extensiones con respuestas de encuesta, controles de disponibilidad y combinaciones | La encuesta aportó información útil; el balance de estimación global todavía tenía limitaciones |
| B + QVoice con ajustes posteriores | Búsqueda de combinaciones, calibración mensual y prueba de un ajuste a seis meses | Ajustar las estimaciones sobre el pasado no aseguró una mejora en el periodo posterior |
| C | Modelo con un conjunto más amplio de información de RH | Mejor balance promedio para continuar con la priorización de grupos |
| `C_Bcuts` | C usando antigüedad × salidas del equipo × nivel, los cortes originales de B | Variante de C elegida para continuar; fuente de la comparación de la diapositiva 5 |
| CQ | C conservado como base más una corrección QVoice seleccionada con la historia disponible en cada origen | Modelo elegido actualmente |
| Mezclas fijas posteriores | Las mismas seis preguntas, con promedio de 33, promedio de 28 o sin promedio | Comprobación adicional; no equivalen al procedimiento histórico de CQ |
| D | Pruebas conjuntas de representaciones QVoice, historia reciente, interacciones y controles de método | No produjo una mejora estable para reemplazar CQ |
| `RSF_Q` | Bosque de supervivencia con QVoice, comparado en el experimento D | Alternativa con captura similar al redondear y mayor error de grupo-mes |

### 4.1 Identificación exacta de CQ

- Versión: `engineering-c-qvoice-20261008-v1`.
- Configuración: [engineering_model_c_qvoice_20261008.json](../config/engineering_model_c_qvoice_20261008.json).
- Modelo final: [trained-model/model.json](../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/trained-model/model.json).
- Corte del artefacto final: 7 de septiembre de 2026.
- Los resultados históricos evalúan las selecciones y modelos de cada periodo, conservados en `folds/`.
- La combinación final utiliza Career Goals, promedio de 33 preguntas, Wellbeing Q8/Q10/Q11 y Confidence Q13/Q17. Sus coeficientes finales no tienen evaluación posterior a su ajuste.
- Q4 y Q12 intervienen dentro del promedio de 33 del artefacto final, sin coeficientes individuales propios en esa combinación.

### 4.2 Identificaciones que no deben confundirse

- Los nombres B y C corresponden a los modelos efectivamente ejecutados en octubre; documentos de diseño anteriores utilizaron esas letras para otras alternativas.
- `C_Bcuts`, `C_selected` y el árbol de C son formas distintas de agrupar resultados. La comparación principal de B con C usa `B_cuts` frente a `C_Bcuts`.
- «Level / 8 groups» del ejemplo se refiere a categorías de nivel. No es el número de diapositivas ni el total de grupos de riesgo.
- B tuvo 22 grupos elegibles en la foto del 26-jul-2026. C con los cortes de B tuvo 20 en la foto del 22-feb-2026. El número de grupos depende de la fecha y de la elegibilidad; no se trasladará automáticamente entre ejemplos.
- En D, la selección final conservó Q4, Q12 y Career. Las señales históricas nuevas quedaron fuera. Al explicar D, decir que se probaron esas señales, sin presentarlas como componentes del ganador final.

## 5. Fuentes de evidencia

Todas las rutas son relativas a la raíz del proyecto, salvo los enlaces, que se resuelven desde este documento. Los identificadores S01–S12 se usarán en el guion y en la trazabilidad del HTML.

| ID | Fuente | Uso |
|---|---|---|
| S01 | [Decisión vigente](../docs/context/model-selection-current.md) | Estado elegido de CQ, argumentos, límites y cierre de D |
| S02 | [Base de Julia](../references/presentations/model-selection/20261005-julia-8-groups/presentacion-eng.html) y [registro](../config/presentations/model-selection-base.json) | Estilo, nueve diapositivas y componente de agrupación |
| S03 | [Resultados de B](../output/analysis/engineering/20261003/playbook-tenure-confirmation-v1/confirmation-results.json) y [informe](../output/analysis/engineering/20261003/playbook-tenure-confirmation-v1/confirmation-report.md) | Modelo B de partida y confirmación histórica |
| S04 | [Agrupaciones de B](../output/analysis/engineering/20261003/playbook-group-selection-v1/group-selection-results.json) y [manifest](../output/analysis/engineering/20261003/playbook-group-selection-v1/group-selection-manifest.json) | Contexto de los grupos y procedencia del ejemplo animado |
| S05 | [B + QVoice anual](../output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2/comparison-results.json) y [informe](../output/analysis/engineering/20261008/qvoice-model-b-annual-lag-v2/informe-modelo-b-qvoice.md) | Nueve variantes iniciales y lectura del resultado |
| S06 | [B + QVoice calibrado](../output/analysis/engineering/20261008/qvoice-model-b-calibrated-v1/comparison-results.json) y [contexto](../docs/context/model-b-plus-qvoice-calibrated.md) | Búsqueda de combinaciones y calibración mensual |
| S07 | [Calibración a seis meses](../output/analysis/engineering/20261008/qvoice-horizon-calibration-v1/comparison-results.json) y [informe](../output/analysis/engineering/20261008/qvoice-horizon-calibration-v1/informe.md) | Resultado del ajuste adicional de B + QVoice |
| S08 | [Comparación de cortes B–C](../output/analysis/engineering/20261008/c-group-selection-v1/results.json) | Cifras de la diapositiva 5 |
| S09 | [Decisión C con cortes de B](../output/analysis/engineering/20261008/model-c-v2/decision-eleccion-c-con-cortes-b.md) | Motivos y límites de la preferencia práctica por C |
| S10 | [C + QVoice](../output/analysis/engineering/20261008/model-c-plus-qvoice-v1/results.json) y [contexto](../docs/context/model-c-plus-qvoice.md) | Procedimiento CQ, periodos, combinación final y límites |
| S11 | [Nuevas combinaciones de encuesta](../output/analysis/engineering/20261009/c-qvoice-mean28-v1/results.json) y [decisión](../output/analysis/engineering/20261009/c-qvoice-mean28-v1/selection-decision.json) | CQ frente a preguntas fijas y promedios; diapositivas 6 y 8 |
| S12 | [Resultados de D](../output/analysis/engineering/20261010/model-d-v1/results.json), [decisión](../output/analysis/engineering/20261010/model-d-v1/selection-decision.json) e [informe](../output/analysis/engineering/20261010/model-d-v1/informe.md) | D, control mensual alternativo y RSF + QVoice |

Consultas guardadas de referencia, que se citarán sin ejecutarlas nuevamente:

- B y agrupaciones: [engineering_person_month_features_playbook_v2_20261003.sql](../queries/profiles/engineering_person_month_features_playbook_v2_20261003.sql), registrada en S04.
- C: [engineering_model_c_person_month_20261008.sql](../queries/profiles/engineering_model_c_person_month_20261008.sql).
- CQ: [engineering_model_c_qvoice_person_month_20261008.sql](../queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql).
- Mezclas de encuesta: [engineering_c_qvoice_mean28_person_month_20261009.sql](../queries/profiles/engineering_c_qvoice_mean28_person_month_20261009.sql).
- B + QVoice, comparación anual S05: [engineering_qvoice_person_month_20261008.sql](../queries/profiles/engineering_qvoice_person_month_20261008.sql), registrada en `model_query`.
- Ajuste de B + QVoice a seis meses, S07: [engineering_qvoice_horizon_calibration_20261008.sql](../queries/profiles/engineering_qvoice_horizon_calibration_20261008.sql).
- D, base de entrada: [engineering_rsf_person_month_20261008.sql](../queries/profiles/engineering_rsf_person_month_20261008.sql).
- D, historia adicional: [engineering_model_d_history_person_month_20261010.sql](../queries/profiles/engineering_model_d_history_person_month_20261010.sql).

La [configuración congelada de D](../output/analysis/engineering/20261010/model-d-v1/frozen-config.json) registra esas dos consultas en `base_query` e `history_query`, y las cuatro auditorías siguientes en `audit_queries`:

- [Recencia de cambios de manager](../queries/audits/engineering_model_d_manager_recency_20261010.sql).
- [Recencia de salidas del equipo](../queries/audits/engineering_model_d_team_recency_20261010.sql).
- [Tamaño del equipo del manager](../queries/audits/engineering_model_d_manager_span_20261010.sql).
- [Intensidad de salidas del equipo](../queries/audits/engineering_model_d_team_intensity_20261010.sql).

Estos enlaces documentan el trabajo realizado; la construcción del deck consume los agregados archivados de sus ejecuciones.

Las narrativas antiguas que dicen «todavía no sustituye a C» se leen como decisiones históricas. S01 registra la elección posterior y vigente, sin borrar el resultado de las reglas originales.

## 6. Contrato de comparación y cifras

### 6.1 Población y unidad de lectura

- Población: Engineering, empleados regulares activos, con RF360 excluido según la foto correspondiente.
- Resultado observado: salida voluntaria durante los seis meses siguientes a cada foto mensual.
- Priorización central: grupos ordenados por riesgo que cubren exactamente 30% de la población mediante una fracción uniforme del grupo del límite.
- Las cifras son promedios con igual peso por periodo. Los periodos contienen varias fotos mensuales.
- Una persona y una salida pueden contribuir a más de una ventana. No se sumarán las exposiciones como si fueran personas o salidas únicas.
- Las comparaciones B–C y C–CQ–D tienen ventanas distintas. Sus porcentajes no forman una serie continua de mejora.

### 6.2 Ventanas que aparecerán en subtítulos o notas

| Familia de comparación | Periodos | Forma de explicarlo |
|---|---|---|
| B frente a C, diapositiva 5 | Feb–jul 2024; ago 2024–ene 2025; feb–jul 2025; ago 2025–ene 2026 | Cuatro periodos históricos; mismos cortes dentro de la comparación |
| C, CQ, mezclas y D, diapositivas 6 y 8 | Ago–dic 2025 y ene–feb 2026 | Dos periodos históricos comunes, con seis meses de seguimiento |
| Agrupación ilustrada de B, diapositiva 3 | Foto del 26-jul-2026 de la base original | Ejemplo de cómo se forman los grupos, identificado con su fecha |

En los dos periodos comunes hay 35474 y 35448 personas distintas, respectivamente. Estos conteos describen cada periodo por separado; no se sumarán. La política aplicada usa QVoice 2024 para 2025 y QVoice 2025 para 2026, respetando el episodio laboral. Esta política anual no acredita por sí misma una fecha real de publicación de resultados.

### 6.3 B frente a C: datos de la diapositiva 5

Fuente S08, `summary["30"]`:

| Medida visible | B, `B_cuts` | C, `C_Bcuts` | Campo |
|---|---:|---:|---|
| Share of exits in priority groups | 45.2% | 45.4% | `metrics.capture_percent` |
| Average gap from actual exits, per 100 people | 0.9 | 0.8 | `metrics.group_mae_pp` |

La diferencia de captura calculada antes de redondear es 0.2657540615600485 puntos porcentuales. Su intervalo del 95% es de −0.32274630372847257 a 0.8476850641226936; C gana en tres de cuatro periodos. Por ello la ganancia de captura al 30% se describe como pequeña y no concluyente. Para evitar una resta aparente inconsistente, la tabla principal mostrará los niveles y no añadirá una etiqueta «+0.3» junto a 45.2 y 45.4.

En las notas puede explicarse el escenario secundario de 40%: captura de 56.4% con B y 57.6% con C. Ese escenario sí cumplió su regla retrospectiva, pero no reemplaza el escenario central de la exposición.

El error de esta diapositiva es `group_mae_pp`. Las diapositivas 6 y 8 usan `group_snapshot_mae_pp`; mantener documentada esta diferencia y no comparar sus valores entre estudios.

### 6.4 C frente a CQ: datos de la diapositiva 6

Fuente principal S11, `summary.<modelo>.scenarios["30"]`; S12 reproduce estas referencias.

| Medida | C | CQ |
|---|---:|---:|
| Share of exits in priority groups | 42.4% | 43.1% |
| Captura exacta, para el cálculo | 42.441570879871044 | 43.10597886408406 |
| Error de grupo-mes, referencia precisa de S12 | 0.994006298315717 | 0.9709330350389753 |

Mensaje secundario visible: **“2.3% smaller average gap from actual exits in priority groups.”**

El 2.3% es una reducción relativa del error, calculada como `100 × (error_C − error_CQ) / error_C`; no son 2.3 puntos porcentuales de riesgo. El aumento de captura es aproximadamente 0.7 puntos porcentuales. Los cálculos usan la precisión original y los textos se redondean al final.

Comparación por periodo para mostrar debajo del gráfico principal:

| Periodo | C | CQ | Lectura |
|---|---:|---:|---|
| Aug–Dec 2025 | 42.1% | 43.5% | Mejora de CQ |
| Jan–Feb 2026 | 42.8% | 42.8% | Empate |

Para obtener estos valores desde S12: localizar `periods[]` por `id` y leer `evaluation.<modelo>.scenarios["30"].metrics.capture_percent`. El objeto de un periodo contiene `metrics`; el resumen general no utiliza esa capa adicional.

### 6.5 Pruebas adicionales: tabla de la diapositiva 8

| Etiqueta visible | Captura al 30% | Lectura visible | Fuente y selección |
|---|---:|---|---|
| C + QVoice · selected | 43.1% | Reference | S12, `summary.CQ.scenarios["30"]` |
| Fixed survey questions + revised average | 43.1% | Same capture; estimates further from actual | S11, `summary.disjoint.scenarios["30"]` |
| D · recent team history tested | 42.8% | Slightly closer estimates; weaker latest period | S12, `summary.D.scenarios["30"]` |
| Alternative method + QVoice | 43.1% | Similar capture; estimates further from actual | S12, `summary.RSF_Q.scenarios["30"]` |

Respaldo para las notas, sin convertirlo en otra tabla densa en pantalla:

- La fila de preguntas fijas representa **media28**, identificada como `disjoint`. Su error de grupo-mes es 4.1% mayor que el de CQ en el mismo estudio.
- Las alternativas `overlap` —promedio 33— e `items_only` —sin promedio— también se probaron. La tabla principal representa la variante con menor error de grupo-mes entre esas tres mezclas nuevas. No se presentará esa fila como si cada alternativa tuviera exactamente el mismo error.
- D reduce el error de grupo-mes aproximadamente 0.8% frente a CQ, por debajo del 10% exigido por su ruta de precisión. Su diferencia media de captura es −0.3 puntos, con intervalo del 95% de −1 a 0.4.
- En ene–feb 2026, CQ captura 42.8% y D 42.1%. D no cumple el límite permitido de pérdida por periodo.
- D seleccionó únicamente Q4, Q12 y Career. La historia reciente adicional no aportó una mejora suficiente para conservarla en la selección final.
- El control `monthly_logit` produjo prácticamente las mismas métricas que D. Se explicará en las notas como comprobación de otra forma de cálculo.
- `C_updated` alcanzó 42.7% de captura y mayor error de grupo-mes que CQ. Es un control adicional para preguntas; no ocupa otra fila principal.
- `RSF_Q` tiene aproximadamente 10.3% más error de grupo-mes que CQ. Su captura es similar al redondear, no exactamente idéntica.
- Las diferencias relativas de error se calculan dentro de cada estudio: `100 × (error_alternativa / error_CQ − 1)`.

### 6.6 Significado que debe conservar la exposición

“43.1% of observed exits came from priority groups covering 30% of Engineering.”

Esta frase describe concentración de salidas en grupos priorizados. No significa que 43.1% de los empleados priorizados saldrá ni que se evitará 43.1% de las salidas. Tampoco se describirá como «43.1% de precisión».

## 7. Guion general y distribución del tiempo

| # | Título visible en inglés | Tiempo | Fin acumulado |
|---|---|---|---|
| 1 | C + QVoice is our selected model | 1:00 | 1:00 |
| 2 | How we moved from B to our current choice | 1:00 | 2:00 |
| 3 | B gave us understandable groups to prioritize | 2:00 | 4:00 |
| 4 | QVoice added useful information to B | 2:00 | 6:00 |
| 5 | C brought estimates closer to actual exits, on average | 2:30 | 8:30 |
| 6 | C + QVoice improved our priorities modestly | 3:00 | 11:30 |
| 7 | Employee feedback refines priorities within familiar groups | 2:00 | 13:30 |
| 8 | Further tests supported keeping C + QVoice | 3:00 | 16:30 |
| 9 | Next: confirm the results in a new period | 1:30 | 18:00 |

Los minutos 18–20 se reservan para preguntas. No se añade una décima diapositiva para ellas. Los detalles complementarios estarán en el guion del presentador y en el documento de evidencia.

## 8. Especificación por diapositiva

### Diapositiva 1 — Decisión y propósito

**Objetivo:** que la audiencia conozca la elección y la pregunta de negocio desde el inicio.

**Título:** “C + QVoice is our selected model”.

**Subtítulo:** “Engineering · Voluntary exits over the next 6 months · October 2026”.

**Disposición:** portada de Julia, con título grande y tres tarjetas horizontales. Texto de las tarjetas:

1. “Prioritize groups” — “Focus attention where more exits are expected.”
2. “Improve estimates” — “Bring group estimates closer to observed exits, on average.”
3. “Keep groups understandable” — “Years at Qualcomm, team exits and level.”

**Nota visible:** “Selected for the next validation stage. A pilot has not started.”

**Evidencia:** S01 y S10. La afirmación de mejora promedio se refiere al balance de CQ frente a C y se sustenta cuantitativamente en la diapositiva 6.

**Notas del presentador:** explicar que el trabajo busca orientar la atención de RH hacia grupos y que se revisará el recorrido desde B. Anticipar que la ganancia es moderada y que se evaluaron alternativas antes de mantener CQ. Reservar las cifras para las comparaciones posteriores.

**Transición:** «Para entender esta elección, veamos qué cambió desde el modelo que presentamos anteriormente».

### Diapositiva 2 — Recorrido de la presentación

**Objetivo:** establecer una secuencia simple y situar las pruebas relacionadas.

**Título:** “How we moved from B to our current choice”.

**Disposición:** agenda vertical de cuatro entradas, con referencia a las diapositivas:

| Diapositivas | Etiqueta visible | Descripción visible |
|---|---|---|
| 3–4 | Our starting point | B and the first QVoice tests |
| 5–7 | What improved | C, employee feedback and the selected approach |
| 8 | Additional checks | Other survey mixes, D and an alternative method |
| 9 | The decision and next step | Keep C + QVoice and check a new period |

Añadir una franja discreta con `B → C → C + QVoice`. B + QVoice y D se mostrarán como pruebas relacionadas, sin sugerir que D sustituyó a CQ.

**Evidencia:** cronología de S03–S12. Esta diapositiva es un mapa del relato, no un gráfico de resultados.

**Notas del presentador:** explicar que cada etapa buscó un mejor balance: encontrar grupos útiles para orientar acciones, aproximarse a lo observado y conservar una explicación comprensible.

**Transición:** «B ya nos daba una base útil y una forma sencilla de describir los grupos».

### Diapositiva 3 — Lo que ya teníamos con B

**Objetivo:** explicar la base común antes de introducir las mejoras.

**Título:** “B gave us understandable groups to prioritize”.

**Disposición:** gráfico de agrupación como elemento principal y una columna estrecha de explicación. Usar el componente de agrupación de la base de Julia (`#wt-plane` y su SVG), reubicado desde la antigua diapositiva 6. Conservar sus datos agregados de B y su fecha; excluir del nuevo contenido las tablas con ejemplos personales de la diapositiva antigua.

**Secuencia animada A:**

1. “All Engineering”.
2. “Years at Qualcomm”.
3. “Team exits”.
4. “Level”.

**Texto de apoyo:**

- “B used information HR already tracks.”
- “Groups made the results easier to discuss.”
- “We then tested whether more information could improve the choice.”

**Nota visible:** “B grouping example · 26 Jul 2026 · Dots summarize groups, not individual predictions.”

El componente debe conservar su significado cuantitativo. Las unidades, pesos de puntos y tamaños se obtendrán de los agregados originales; cualquier leyenda numérica reutilizada deberá comprobarse contra S04. Retirar indicadores secundarios sobre Gini, eficiencia o comparación con ranking individual de la vista principal para mantener el mensaje sencillo.

**Evidencia:** S02, S03 y S04. Las agrupaciones ilustran B; no representan las cifras comparativas de C o CQ.

**Notas del presentador:** recorrer los tres criterios con un ejemplo de grupo expresado por categorías, sin nombres ni predicciones personales. Explicar que el modelo utiliza más información para estimar, mientras esos tres criterios permiten resumir los resultados. La animación no demuestra causas de salida.

**Transición:** «La primera pregunta fue qué podíamos aprender de lo que los empleados nos habían dicho en QVoice».

### Diapositiva 4 — Lo que aprendimos con B + QVoice

**Objetivo:** mostrar el trabajo realizado y por qué una mejora parcial no cerró la selección.

**Título:** “QVoice added useful information to B”.

**Disposición:** tabla de tres filas y tres columnas, con texto breve:

| What we tested | What improved | What still needed work |
|---|---|---|
| Individual survey questions and combinations | Better separation of higher and lower risk | Overall estimates did not meet the agreed comparison rule |
| Broader survey combinations | Useful information beyond response availability | Overall estimates still had limitations |
| Additional adjustments to estimated risk | Better fit to earlier data | The improvement did not carry over consistently |

**Mensaje al pie:** “Employee feedback was useful; we continued testing the overall balance.”

**Evidencia:** primera fila S05; segunda S06; tercera S07. No mezclar las métricas de B + QVoice con las de CQ en una misma columna.

**Notas del presentador:** las nueve variantes iniciales mejoraron medidas de ordenamiento y error promedio, pero ninguna cumplió todas las comprobaciones históricas. Q4 fue una alternativa sencilla y prometedora. Las búsquedas posteriores y los ajustes adicionales no resolvieron de forma consistente la cercanía del total estimado al observado. Explicar estas ideas sin pronunciar nombres de medidas estadísticas.

**Límite de la conclusión:** el resultado no invalida QVoice ni demuestra que una calibración siempre sea inútil. Describe lo que funcionó y lo que quedó pendiente en estas pruebas.

**Transición:** «También ampliamos la información de RH y comprobamos si C mejoraba el balance manteniendo grupos conocidos».

### Diapositiva 5 — Por qué continuamos con C

**Objetivo:** justificar el paso B → C con una comparación válida y proporcional a la evidencia.

**Título:** “C brought estimates closer to actual exits, on average”.

**Subtítulo:** “B and C · Same group definitions · 4 historical periods · Priority groups covering 30% of Engineering”.

**Disposición:** tabla central de dos modelos y dos medidas, utilizando exactamente la tabla de la sección 6.3. Debajo, tres etiquetas: “More HR information”, “Familiar groups”, “Small average improvement”.

**Nota visible:** “The gain in the share of exits was small and remained uncertain.”

**Evidencia:** S08 y S09. Seleccionar `B_cuts` y `C_Bcuts`, nunca el árbol de ocho hojas ni `C_selected`.

**Notas del presentador:** C conserva una captura parecida y reduce el error promedio por grupo. La preferencia fue práctica, orientada a grupos prioritarios e interpretación. C no ganó todas las medidas en todas las fechas. Si se pregunta por la fuerza de la evidencia, explicar el intervalo de captura que incluye cero y el resultado favorable del escenario secundario del 40%.

**Transición:** «Con esa base, volvimos a comprobar qué añadía la información de QVoice».

### Diapositiva 6 — Qué añadió QVoice a C

**Objetivo:** presentar el beneficio concreto que apoya la elección de CQ.

**Título:** “C + QVoice improved our priorities modestly”.

**Subtítulo:** “Share of observed exits in priority groups covering 30% of Engineering · Next 6 months”.

**Disposición:** dos barras horizontales sobre una misma escala de 0% a 50%, etiquetadas directamente: C, 42.4%; C + QVoice, 43.1%. Añadir una tarjeta de apoyo con la reducción relativa de error de 2.3% y una tabla pequeña de los dos periodos de la sección 6.4.

**Secuencia animada B:** revelar primero C y después CQ. Los valores finales se mantienen escritos; la animación no cuenta cifras intermedias. Al completar la secuencia se destaca la nota de mejora modesta.

**Nota visible:** “Improved in Aug–Dec 2025; tied in Jan–Feb 2026. Historical comparison; average results.”

**Evidencia:** S10, S11 y reconciliación con S12. Fechas de evaluación: ago–dic 2025 y ene–feb 2026, seguimiento hasta agosto de 2026.

**Notas del presentador:** definir la medida con la frase de la sección 6.6. Explicar que se usa el mismo porcentaje de población para comparar, aunque las prioridades puedan cambiar. CQ combina algo más de concentración de salidas con un error de grupo-mes ligeramente menor. No gana captura en los dos periodos; gana uno y empata el otro. Algunos grupos concretos siguen peor estimados.

**Transición:** «La encuesta refina las prioridades y los grupos continúan siendo fáciles de describir».

### Diapositiva 7 — Cómo se entiende la opción elegida

**Objetivo:** explicar CQ sin fórmulas y distinguir la versión final de los modelos evaluados por periodo.

**Título:** “Employee feedback refines priorities within familiar groups”.

**Disposición:** diagrama a ancho completo con tres estaciones:

1. “HR information” — “Work history and team context”.
2. “Employee feedback” — “Career goals · Overall feedback · Wellbeing · Confidence”.
3. “Priority groups” — “Years at Qualcomm · Team exits · Level”.

La estación de QVoice se conecta a la estimación y después al orden de los grupos. El diagrama es conceptual: no contiene personas, riesgos inventados, tamaños de grupo simulados ni movimientos de posición que parezcan resultados medidos.

**Secuencia animada C:** mostrar la base de RH, añadir la capa de QVoice y finalmente resaltar las definiciones de grupo. Conservar las etiquetas durante las transiciones.

**Notas visibles:**

- “Final September version: survey topics shown above.”
- “Historical tests used the model available at each date. The final version still needs a check using later data.”

**Evidencia:** S01 y S10; cotejar los temas con la configuración y el artefacto final de CQ.

**Notas del presentador:** la combinación final reúne desarrollo profesional, valoración general, bienestar y confianza. Las preguntas elegidas variaron entre orígenes históricos. Esta imagen describe la combinación final, mientras la comparación anterior evalúa el procedimiento a lo largo del tiempo. Las respuestas de una encuesta se utilizaron al año siguiente, según la política aplicada.

**Transición:** «Antes de cerrar la elección, comprobamos otras combinaciones y un modelo adicional».

### Diapositiva 8 — Por qué D y las otras pruebas no cambiaron la elección

**Objetivo:** demostrar que la elección se contrastó con alternativas y explicar el resultado sin presentar D como un éxito superior.

**Título:** “Further tests supported keeping C + QVoice”.

**Subtítulo:** “Same two historical periods · Priority groups covering 30% of Engineering”.

**Disposición:** tabla de cuatro filas de la sección 6.5. La fila CQ tiene el color de énfasis y la etiqueta “Selected”. Las alternativas usan tonos de contexto y conclusiones escritas.

**Anotación principal:** “Latest period: CQ captured 42.8% of exits; D captured 42.1%.”

**Nota secundaria:** “New team history signals did not add enough value to remain in D's selected version.”

**Evidencia:** S11 para las mezclas fijas; S12 para D y la alternativa. El texto sobre el periodo reciente se obtiene de `periods[id="jan_feb_2026"]`.

**Notas del presentador:** media28 conservó la misma captura con mayor error de grupo-mes. D acercó ligeramente las estimaciones, pero su captura fue menor y perdió más en el periodo reciente de lo permitido. El método alternativo tuvo una captura similar con mayor error de grupo-mes. Se conservó CQ por ese balance. Las pruebas negativas también son un resultado del trabajo: delimitan qué cambios no aportaron una mejora estable bajo esta comparación.

**Detalles para preguntas:** otras mezclas con promedio 33 o sin promedio, C actualizado, control mensual alternativo, criterio de precisión de D y limitación de contar con dos encuestas anuales. Permanecen en las notas, sin ampliar la tabla principal.

**Transición:** «Con estas comprobaciones, la decisión se mantiene y el siguiente paso es contrastarla con un periodo nuevo».

### Diapositiva 9 — Decisión y siguiente comprobación

**Objetivo:** terminar con una decisión inequívoca y pasos realistas.

**Título:** “Next: confirm the results in a new period”.

**Disposición:** cierre con una frase principal y tres pasos grandes:

**Frase principal:** “C + QVoice remains our selected model.”

1. “Check a new period” — “Evaluate the final version after its training date.”
2. “Review priority groups” — “Check how close estimates are to actual exits.”
3. “Prepare a limited pilot” — “Define the scope, owners and measures before starting.”

**Nota visible:** “Historical results support selection. The effect of retention actions still needs to be measured.”

**Evidencia:** S01 y límites de S10–S12. Estos son pasos propuestos; no se presentarán como actividades ya ejecutadas, fechas comprometidas o un piloto aprobado.

**Notas del presentador:** repetir la elección en una frase, recordar que la ganancia es moderada y explicar que el siguiente periodo debe evaluar el artefacto final. Terminar alrededor del minuto 18 y utilizar esta misma diapositiva durante las preguntas.

## 9. Especificación visual e interacción

### 9.1 Lectura y composición

- Un mensaje principal por diapositiva. Los gráficos y tablas se agrupan únicamente cuando sostienen esa misma conclusión.
- Título habitual de 30–36 px; portada de aproximadamente 44 px. Cuerpo de 18–22 px cuando el espacio lo permita; celdas y etiquetas clave de al menos 16 px. Fuentes de 12–14 px, sin convertirlas en explicación principal.
- Mantener la tipografía, espaciado, tarjetas y controles de Julia. Ajustar el contenido antes de reducir la letra.
- Usar un color de énfasis para la elección y tonos neutros para el contexto. Las conclusiones deben entenderse también sin color.
- En barras, origen en cero y misma escala dentro de cada comparación. La escala 0–50 de la diapositiva 6 incluye las cifras completas y evita exagerar la diferencia.
- Tablas numéricas con cifras alineadas a la derecha, encabezados breves y unidades explícitas.
- Enteros sin decimales; no enteros con máximo un decimal. Aplicar también a tooltips, contadores, leyendas y etiquetas de animación.

### 9.2 Imágenes y recursos

- Reutilizar el gráfico agregado de B de la base y construir el diagrama conceptual de CQ con SVG integrado.
- Las imágenes se incorporan como SVG o datos embebidos; añadir texto alternativo que explique el mensaje.
- Los gráficos nuevos de esta versión son sencillos y pueden resolverse con HTML/CSS/SVG y JavaScript integrado. El componente heredado de Julia puede conservar su soporte ya embebido como parte de la base solicitada.
- La versión final debe abrir directamente y funcionar sin red. No depender de archivos vecinos, fuentes descargadas o bibliotecas externas nuevas.

### 9.3 Comportamiento exacto de las animaciones

| Animación | Diapositiva | Estados | Controles |
|---|---|---|---|
| A: grupos de B | 3 | Todos → antigüedad → salidas del equipo → nivel | `Play`, `Replay`, `Show all`, selección directa de cada estado |
| B: comparación C–CQ | 6 | C → C + QVoice → conclusión | `Play`, `Replay`, `Show all` |
| C: explicación CQ | 7 | RH → QVoice → grupos prioritarios | `Play`, `Replay`, `Show all` |

- Duración de una transición visual: entre 400 y 700 ms. La secuencia completa no debe superar 6 segundos.
- Las animaciones comienzan únicamente al pulsar `Play`; el cambio de diapositiva no inicia reproducción automática.
- `Replay` reinicia la secuencia. `Show all` muestra inmediatamente el estado final.
- Al salir de una diapositiva se cancelan temporizadores pendientes. Al volver se muestra su estado inicial con controles disponibles.
- Con `prefers-reduced-motion`, mostrar inmediatamente el estado final y conservar toda la información.
- Los botones deben funcionar con teclado. Las flechas continúan navegando entre diapositivas; no se reasignan a una segunda función.
- Mantener controles y valores en posiciones estables para evitar saltos de disposición.

## 10. Lenguaje y notas del presentador

### 10.1 Vocabulario visible

| Concepto de respaldo | Expresión que se usará en la presentación |
|---|---|
| Features o variables | HR information / survey information |
| Captura al 30% | Share of observed exits in priority groups |
| Error absoluto de grupo | Average gap from actual exits |
| Validación temporal | Checks using earlier periods |
| Calibración | Additional adjustment to estimated risk |
| Modelo por fold | Model available at that date |
| Offset y corrección QVoice | HR information refined with employee feedback |
| RSF + QVoice | Alternative method + QVoice |

Las fórmulas y términos `hazard`, `cloglog`, `L1`, `L2`, `PCA`, `Brier`, `PR-AUC`, `log-loss`, `bootstrap` y `fold` quedan en el respaldo para implementación y preguntas técnicas, fuera del contenido proyectado. Los nombres B, C, CQ y D se introducen con su significado cotidiano.

### 10.2 Contenido del guion en español

Crear `guion-presentador.md` junto al HTML. Para cada diapositiva contendrá:

1. Objetivo y duración, con tiempo acumulado.
2. Explicación hablada sugerida basada en las notas de la sección 8.
3. Momento de activar la animación, cuando aplique.
4. Cifra o contraste que debe recordar la audiencia.
5. Limitación que cambia la interpretación.
6. Frase de transición a la siguiente diapositiva.

Añadir respuestas breves para estas preguntas:

- ¿Por qué no conservar B? Preferencia práctica por el balance de C usando cortes conocidos; mejora pequeña y limitada al alcance evaluado.
- ¿Por qué CQ si no ganó ambos periodos? Ganó uno y empató otro en captura, con menor error promedio de grupo-mes. La decisión incorpora magnitud, utilidad y claridad; no cambia el resultado de la regla histórica más estricta.
- ¿Una captura de 43.1% significa que esas personas se irán? Es una proporción de las salidas observadas concentrada en grupos, no una probabilidad personal.
- ¿D fue peor en todo? No. Acercó ligeramente las estimaciones, pero no alcanzó el balance requerido y perdió captura en el periodo reciente.
- ¿QVoice provoca las salidas? El estudio identifica asociaciones predictivas; no demuestra causas.
- ¿Qué contiene exactamente el CQ elegido? La versión identificada en 4.1; distinguir la combinación final de las selecciones históricas.
- ¿Ya está probado el modelo final de septiembre? Sus coeficientes finales requieren una evaluación posterior a su ajuste.
- ¿Por qué 30%? Es el escenario central de comparación; la capacidad operativa debe definirse para un eventual piloto.
- ¿Ya se están evitando salidas? No se ha evaluado el efecto de intervenciones; el piloto todavía no comenzó.
- ¿Por qué cambiaron los porcentajes entre las diapositivas 5 y 6? Corresponden a conjuntos distintos de periodos; no representan deterioro ni mejora de una única serie.

## 11. Construcción y entregables

### 11.1 Archivos que se crearán al implementar

| Archivo propuesto | Función |
|---|---|
| `tools/presentations/build_model_evolution_b_cq.py` | Construcción reproducible desde la base vigente y agregados existentes |
| `config/presentations/model-evolution-b-cq-20261010.json` | Fuentes, correspondencias, nueve diapositivas, tiempos e idioma |
| `<carpeta de salida>/presentacion-eng.html` | Presentación autónoma |
| `<carpeta de salida>/guion-presentador.md` | Notas, tiempos y respuestas |
| `<carpeta de salida>/evidence.json` | Relación entre cifras, fuentes, campos, transformaciones y textos publicados |
| `<carpeta de salida>/validation.json` | Comprobaciones de datos, estructura, idioma, navegación y revisión visual |
| `output/preview/<misma ejecución>/` | Capturas y hoja de contacto de las nueve diapositivas |

El script nuevo aceptará `--out <ruta-nueva.html>`; por defecto creará una carpeta con fecha y hora local bajo `output/presentations/`. Si la ruta existe, debe detenerse y pedir una ruta nueva al invocador, sin sobrescribir una entrega anterior. La interfaz nueva es un constructor de presentación; no expone entrenamiento ni predicción.

### 11.2 Orden de implementación

1. Leer las instrucciones y las fuentes citadas. Confirmar la referencia S01 y comprobar el hash de la base S02.
2. Preparar un inventario de agregados para las diapositivas 5, 6 y 8, con las correspondencias de la sección 6. Revisar la equivalencia de CQ entre S11 y S12 antes de combinarlas en la exposición.
3. Crear la especificación de presentación con los títulos, tiempos, fuentes y textos aquí definidos. El total de tiempos será 1080 segundos.
4. Exportar una copia de la base vigente utilizando el flujo normal del exportador, preservando el escenario y los bloques centrales de navegación y temas.
5. Sustituir el contenido de las nueve diapositivas y sincronizar sus nueve botones de navegación. Reubicar el componente agregado de B y conservar sus datos y procedencia.
6. Construir las tablas, barras y el diagrama conceptual. Los datos visibles proceden del inventario de agregados, con redondeo exclusivamente al mostrar.
7. Añadir controladores de animación después de los bloques centrales existentes. `showSlide` y `applyTheme` están encapsulados; no asumir que son funciones globales. Detectar cambios de diapositiva mediante el estado del DOM y los controles ya existentes.
8. Incorporar notas de fuente breves y el guion en español. Completar el documento de evidencia.
9. Ejecutar las comprobaciones de la sección 12, corregir los hallazgos y volver a comprobar únicamente lo afectado.
10. Entregar el enlace al HTML y al guion, indicando el resultado de las verificaciones y cualquier excepción documentada.

### 11.3 Contenido mínimo del registro de evidencia

Para cada afirmación numérica: identificador de diapositiva, identificador de afirmación, fuente, SHA-256, fecha del estudio, población, periodo, consulta guardada o referencia a su manifest, campo JSON, valor original, cálculo aplicado y texto final mostrado.

Para cada afirmación cualitativa: fuente, sección que la respalda, alcance y limitación relevante. Las conclusiones de los modelos se reproducen desde la evidencia histórica; este registro no es un assessment ni asigna scores a variables.

Conservar en el registro la identidad de la base, la versión CQ elegida, los 9 tiempos, `language: en` y `deliverable_classification: presentation`.

### 11.4 Fuentes visibles en el HTML

Cada visual cuantitativo llevará una nota breve en inglés con estudio, fecha, población, ventana y medida. Ejemplos:

- Diapositiva 5: “Engineering · Active regular employees, excluding RF360 · 4 historical periods · 6-month exits · 8 Oct 2026 analysis.”
- Diapositivas 6 y 8: “Engineering · Active regular employees, excluding RF360 · Aug–Dec 2025 and Jan–Feb 2026 snapshots · 6-month follow-up · 9–10 Oct 2026 analyses.”

La ruta exacta del resultado y de la consulta se documentará en el guion y en `evidence.json`. Se pueden asociar identificadores breves de fuente a las notas del HTML para conectar ambas lecturas sin llenar la proyección de rutas técnicas.

## 12. Comprobaciones y criterios de aceptación

### 12.1 Evidencia

- [ ] Se identifica exactamente `engineering-c-qvoice-20261008-v1` como CQ.
- [ ] Cada cifra visible coincide con su campo fuente después del redondeo previsto.
- [ ] CQ de S11 y S12 coincide en las medidas usadas, dentro de una tolerancia numérica de `1e-8`.
- [ ] Los porcentajes de captura no se presentan como probabilidades de salida ni como salidas evitadas.
- [ ] B–C usa cuatro periodos; C–CQ–D usa dos periodos comunes. Ningún gráfico los conecta como una única evolución numérica.
- [ ] Se distingue `group_mae_pp` de `group_snapshot_mae_pp` en la trazabilidad.
- [ ] El 2.3% es reducción relativa de error; la ganancia de captura de CQ es aproximadamente 0.7 puntos.
- [ ] El relato incluye mejora de CQ en un periodo y empate en otro.
- [ ] La fila de mezcla fija corresponde a `disjoint`, no al artefacto CQ elegido.
- [ ] El método alternativo tiene captura similar al redondear; no se afirma un empate exacto.
- [ ] D se presenta como una prueba que no alcanzó el balance requerido, reconociendo su pequeña mejora de estimación.
- [ ] La combinación final de septiembre se distingue de los modelos históricos evaluados.

### 12.2 Estructura e idioma

- [ ] Exactamente 9 elementos `.slide-stage` y 9 botones `.nav-pill`.
- [ ] IDs de diapositiva únicos e índices de navegación de 0 a 8.
- [ ] Agenda en la posición 2, con correspondencia correcta de páginas.
- [ ] `lang="en"` y clasificación `<meta name="deliverable-classification" content="presentation">`.
- [ ] Cuerpo visible en inglés y guion explicativo en español.
- [ ] El deck abre en la primera diapositiva; únicamente el tema se conserva entre aperturas.
- [ ] Enteros sin decimales y demás cifras con máximo un decimal, incluyendo contenido dinámico.

### 12.3 Particularidad del verificador existente

El verificador leído al elaborar el plan es [verify_deck.py](../.agents/skills/build-html-presentation/scripts/verify_deck.py). Su interfaz actual acepta el archivo y `--mode`, y exige siempre `lang="es"`. No tiene un parámetro para autorizar inglés. También avisa cuando encuentra etiquetas como `Theme` o `Slides`.

Ejecutar el verificador original sobre el resultado real y conservar íntegra su salida:

```powershell
.\.venv\Scripts\python.exe -B .agents/skills/build-html-presentation/scripts/verify_deck.py <ruta-del-html> --mode presentation
```

Resolver esta discrepancia de manera explícita en la validación del deck:

1. Mantener `lang="en"`, porque es la elección confirmada por el usuario y la base vigente.
2. Registrar el error exacto `El elemento <html> debe declarar lang="es".` como excepción de idioma prevista para este entregable, junto con la referencia a la sección 2 del plan y a la base.
3. Registrar del mismo modo los avisos de controles en inglés cuando correspondan a la preferencia confirmada.
4. Comprobar por separado que títulos, tablas, controles y notas visibles son coherentes con `lang="en"`.
5. Resolver cualquier otro error o aviso material. La excepción de idioma no cubre privacidad, cifras, recursos, estructura ni problemas visuales.

El informe final de validación distinguirá «verificador original con excepción documentada de idioma» de «verificador sin errores». No cambiar el idioma declarado para forzar un resultado favorable, ni modificar el skill global únicamente por este deck.

### 12.4 Navegador, accesibilidad y proyección

- [ ] Abrir a 1440 × 810 y recorrer las nueve diapositivas en los cuatro temas.
- [ ] Revisar también a 1920 × 1080 para confirmar escalado en proyección.
- [ ] Guardar capturas y una hoja de contacto bajo `output/preview/`.
- [ ] No hay recortes, superposiciones, gráficos vacíos ni texto principal ilegible.
- [ ] Flechas, botones y controles de animación funcionan sin interferirse.
- [ ] Salir de una diapositiva cancela su reproducción; volver permite reiniciarla.
- [ ] `Show all` y movimiento reducido preservan todas las conclusiones y datos.
- [ ] Las tablas y gráficos se comprenden sin depender únicamente del color.
- [ ] El HTML se abre sin red y los recursos están integrados.
- [ ] No hay errores de JavaScript ni fallos de carga de recursos necesarios.

### 12.5 Datos y privacidad

- [ ] El HTML y su JavaScript contienen únicamente agregados permitidos y parámetros de presentación.
- [ ] No hay filas de empleados, identificadores, nombres, correos, respuestas individuales ni puntuaciones personales.
- [ ] No se reutilizan las tablas de ejemplos personales del deck antiguo.
- [ ] Los puntos de la agrupación representan agregados y se rotulan como tales.
- [ ] Las cohortes y tasas mostradas respetan los mínimos del estudio y del modo `presentation`.
- [ ] Las etiquetas protegidas y los valores de compensación individuales quedan fuera de todos los artefactos.

### 12.6 Narrativa y tiempo

- [ ] Al terminar, la audiencia puede explicar B → C → CQ y el papel de D.
- [ ] Se comunica una ganancia modesta, sin presentar superioridad universal.
- [ ] El estado de QVoice y del método alternativo se actualiza respecto a los pendientes del ejemplo de Julia.
- [ ] Se explica que el piloto no comenzó y que la versión final requiere una comprobación posterior.
- [ ] El recorrido con las tres animaciones cabe en 18 minutos, dejando 2 para preguntas.
- [ ] La revisión visual aplica el checklist de `morgan-vis`: un mensaje, comparación pertinente, escalas honestas, etiquetas directas y límites comprensibles.

## 13. Casos que requieren una corrección antes de entregar

| Hallazgo | Acción definida |
|---|---|
| Falta un archivo de evidencia o un campo previsto | Identificar la referencia exacta en el manifest del estudio; no completar una cifra por intuición |
| Una cifra narrativa difiere del JSON | Revisar población, periodo, variante, campo y redondeo; documentar la resolución antes de publicarla |
| El hash de la base no coincide | Verificar el registro y la copia de referencia; evitar construir sobre un archivo distinto sin identificar el cambio |
| El contenido no cabe | Acortar texto secundario y trasladar explicación al guion, preservando nueve diapositivas y letra legible |
| El gráfico heredado conserva contenido personal o técnico innecesario | Extraer únicamente el componente agregado y su soporte; comprobar el HTML completo, incluido JavaScript |
| Una animación pierde datos o altera la navegación | Corregir su controlador; mantener una vista completa disponible con `Show all` |
| Una prueba adicional necesitaría otra diapositiva | Incorporar el detalle en el guion y en evidencia; mantener la selección de filas de la diapositiva 8 |
| Se solicita un periodo nuevo de datos o entrenamiento | Registrar el cambio de alcance; este plan utiliza las ejecuciones archivadas hasta el 10-oct-2026 |

## 14. Definición de terminado

La implementación estará completa cuando existan el HTML de nueve diapositivas, el guion en español y los registros de evidencia y validación; las cifras estén reconciliadas; la presentación funcione sin red en los cuatro temas; las tres animaciones sean utilizables y opcionales; y el relato se haya ensayado dentro de 18 minutos.

El contenido debe permitir comprender y defender esta conclusión con sus límites: **CQ es la elección vigente para continuar; aporta una mejora promedio modesta sobre C, conserva grupos interpretables y las alternativas probadas, incluido D, no demostraron un mejor balance estable. La comprobación posterior del artefacto final sigue pendiente.**
