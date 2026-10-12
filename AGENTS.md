# Instrucciones del proyecto Attrition

Estas reglas aplican a todo el workspace.

## Fuentes de estado del proyecto

- Antes de cambiar o comparar modelos, consulta
  [la decisión vigente](docs/context/model-selection-current.md).
  A 12-oct-2026 sigue elegido **CQ** (`engineering-c-qvoice-20261008-v1`),
  confirmado el 10-oct-2026, sin calibración adicional de R6.
- La ronda `engineering-b-playbook-v11-20261012-v1` conserva las variables
  de B y prueba incorporaciones RH/QVoice. Su `final-B_RH-Q.json` es
  **experimental**: no sustituyó a CQ ni se comparó directamente con C/CQ
  en esa ejecución. Consulta [su contexto y documentación](docs/context/b-playbook-v11-documentacion-variables.md).
- [docs/README.md](docs/README.md) es el índice de entrada. Mantén las
  decisiones, resultados y límites en los documentos de contexto y en los
  artefactos de cada ejecución; aquí conserva instrucciones y referencias.
  El nombre `final` de un artefacto no implica que sea el modelo elegido.

## Skills obligatorios

- Usa `attrition-redshift-db` para toda inspección o consulta a Redshift.
- Usa además `evaluate-attrition-variable` cuando se evalúe disponibilidad,
  definición, cobertura, missingness, consistencia, historia, join, esfuerzo o
  score de una variable.
- Usa `build-html-presentation` para crear, editar o verificar decks HTML.
  Aplica `morgan-vis` al diseñar gráficos, tablas, KPIs y narrativa visual.
- Lee las reglas y referencias completas que esos skills indiquen antes de
  consultar o generar un assessment.

## Puerta de evidencia para score 2

- No asignes un 2 cualitativo por el nombre de una columna, un caption de
  Tableau, una interpretación habitual, un documento narrativo ni un workbook
  anterior.
- Antes del 2, define exactamente la afirmación, clasifica el tipo semántico,
  guarda una consulta agregada en `queries/audits/` o
  `queries/profiles/`, declara la regla de aceptación y ejecútala.
- Registra método, evidencia, resultado, fecha, ruta SQL, regla de aceptación,
  `outcome: pass` y las métricas agregadas exigidas.
- Métricas precalculadas y features derivadas requieren recálculo independiente
  o lineage oficial más reconciliación agregada sobre el campo y población
  objetivo.
- Jerarquías requieren raíces, convergencia, ciclos, cadenas no resueltas y
  profundidad reconstruida. Converger en una persona no demuestra por sí solo
  que sea el CEO definido por negocio.
- Agrupaciones requieren validar contradicciones detalle-grupo y cambios del
  mapping en el tiempo. La cardinalidad no demuestra que el mapping sea
  correcto.
- Si algo no se puede confirmar, usa 1 o 0 con explicación; no rellenes
  evidencia para conservar un puntaje previo.

## Datos y privacidad

- Sólo consultas read-only y resultados agregados.
- Clasifica cada entregable antes de consultar o renderizarlo. Si el usuario
  declara expresamente que es un **análisis interno/exploratorio** para su
  revisión, se pueden mostrar las etiquetas reales de categorías protegidas
  (por ejemplo, los valores registrados de `gender`) y sus conteos o
  porcentajes agregados. El artefacto debe marcarse como `internal_analysis`.
  Para una presentación, entrega compartible o cuando el destino no esté
  claro, usa `presentation`: suprime o anonimiza esas etiquetas.
- En ambos modos, no muestres ni guardes filas de empleados, IDs, nombres,
  correos, domicilios, texto libre ni valores individuales. La compensación
  exacta sigue restringida: en análisis interno sólo se permiten bandas,
  percentiles o estadísticos agregados; no valores por persona.
- Mantén cohortes compartidas de al menos 30 como regla general. Una excepción
  explícita para `internal_analysis` puede autorizar conteos agregados menores
  para una audiencia nominal de desarrolladores, pero debe quedar registrada
  en `config/`, en la evidencia y en el manifest; nunca permite filas,
  identificadores, requisiciones, nombres, acceso de managers, redistribución,
  uso operativo ni cambio de score o producción. La excepción vigente para
  aplicaciones es `config/application_intensity_internal_analysis_authorization_20260913.json`.
- Los IDs pueden usarse internamente en joins y `COUNT(DISTINCT ...)`, pero no
  deben salir en resultados.
- La excepción existente para entrenamiento y validación en memoria está en
  `config/attrition_model_in_memory_training_authorization_20261001.json`.
  Lee su alcance antes de usarla: permite observaciones persona-mes sólo en
  RAM, sin seleccionar IDs de empleado ni persistir filas, cachés o scores
  individuales. Mantiene las exclusiones de atributos protegidos, texto libre
  y compensación exacta; cada manifest debe citar la autorización y declarar
  `employee_level_rows_persisted=false`. No amplía la autorización a otros usos.

## Organización de archivos

- `docs/context/`: contexto general y metodología.
- `docs/variables/<concepto>/`: explicación y decisiones por concepto.
- `docs/plans/`: planes de análisis y estado de preparación.
- `config/`: specs ejecutables. El inventario v2 actual es histórico hasta
  migrarlo con evidencia v4.
- `queries/audits/`: comprobaciones semánticas, de fórmula, mappings,
  jerarquía, consistencia y joins.
- `queries/profiles/`: SQL que devuelve el contrato de cobertura por fecha.
- `output/assessments/`: ejecuciones agrupadas por run con manifest, JSON, Excel, evidence y notebooks; no
  sobrescribir resultados anteriores.
- `output/analysis/<población>/<fecha>/<run>/`: experimentos de modelado,
  modelos, selecciones, resultados, evidencia y verificaciones. Conserva las
  ejecuciones terminadas; genera otra carpeta para una nueva prueba.
- `output/analysis/.../<run>/documentacion/fichas/`: tratamiento ejecutado de
  cada representación, enlazado desde `docs/context/`. Es distinto de la
  documentación conceptual en `docs/variables/`.
- `planes/`: planes y entregables solicitados en esa ubicación. El archivo
  [43_variables_playbook_modelo_final_20261012.md](planes/modelo_c/43_variables_playbook_modelo_final_20261012.md)
  es el **resumen para Julia**; los detalles permanecen en las fichas de la
  ejecución. Los otros MD de `planes/modelo_c/` describen el CQ anterior.
- `references/`: fuentes y binarios de entrada; no tratarlos como outputs.
- `tools/`: scripts auxiliares. No dejar documentos sueltos en la raíz.

Los documentos conceptuales aportan contexto, pero los hallazgos dependientes
de datos deben citar la consulta guardada, fecha, población y métricas.

## Playbook y documentación de modelado

- En esta ronda, «las 43 variables» se refiere a
  `output/distribution/attrition-43-variable-distributions-v11.html` y a su
  correspondencia `config/b_playbook_v11_scope_20261012.json`; no lo sustituyas
  por el inventario histórico de 43 ideas. V11 contiene 42 vistas analíticas,
  con conceptos compartidos y múltiples representaciones. El resumen para
  Julia tiene 43 filas al separar Región y Mercado laboral.
- Para cada representación documenta fuente, valores, tipo de entrada,
  codificación/bandas, transformaciones, faltantes y valores por defecto,
  fecha de conocimiento, pruebas, resultados y decisión por corte.
  Extrae las categorías y referencias finales del modelo guardado.
- Distingue exclusión previa, historia insuficiente, incumplimiento de
  validación y alternativa admisible que no ganó. Las variables obligatorias
  de B no tuvieron una prueba de eliminación. No atribuyas un efecto medido
  a una variable que no pudo probarse ni declares inútil una variable por una
  única codificación. Las recodificaciones propuestas siguen siendo hipótesis
  hasta ejecutarlas.
- Distingue predictor, indicador codificado y grupo de reporte. Compara
  estimadores sobre las mismas personas, fechas, horizonte, capacidad y
  grupos para atribuirles una mejora. Si evalúas otras agrupaciones, declara
  ese cambio y conserva un contraste sobre grupos comunes. Las métricas de
  selección histórica por corte no validan prospectivamente los coeficientes
  del artefacto final.

## Bases de las presentaciones del modelo

- Para el deck HTML de selección del modelo, la base vigente parte de la versión
  de Julia adoptada el 5-oct-2026 y los ajustes pedidos por el usuario, registrados en
  `config/presentations/model-selection-base.json`.
- El archivo recibido es `output/presentations/presentacion-eng.html`; su copia
  exacta está en `references/presentations/model-selection/20261005-julia/`.
  La ruta de la revisión vigente se toma del registro; incluye el ajuste
  del slide 5 a «Level / 8 groups». Conserva su idioma inglés, textos, orden y diseño; aplica sólo los cambios
  pedidos sobre una copia nueva de esa base.
- `tools/presentations/build_model_selection_deck_v9.py` exporta la base vigente
  por defecto. `--historical` reproduce la v9 anterior; no usarla como base de
  nuevas revisiones. El flujo está documentado en `tools/presentations/README.md`.
- El deck de **evolución B → C → CQ** es otro entregable: su configuración es
  `config/presentations/model-evolution-b-cq-20261010.json` y su generador es
  `tools/presentations/build_model_evolution_b_cq.py`. Para editar una revisión
  existente, parte de la ruta indicada por el usuario y crea una copia nueva;
  no deduzcas su adopción sólo por tener una fecha más reciente.
- Conserva en inglés el texto proyectado de esos decks; guion, evidencia y
  documentación analítica permanecen en español. Identifica el modelo y la
  ejecución de cada cifra antes de incorporarla a una diapositiva.

## Ciclo razonado por variable

- Evalua una lista secuencialmente y termina los artefactos de una variable
  antes de iniciar la siguiente.
- Antes de ejecutar Python, define para la variable actual el concepto, uso en
  attrition, fecha de conocimiento, poblacion, grain, tipo semantico y
  validaciones especificas.
- Python ejecuta SQL, reglas, scoring y render; no sustituye el razonamiento que
  determina que consultas, reconciliaciones, casos limite y graficos necesita
  cada concepto.
- Revisa los resultados agregados antes de finalizar. Si revelan una brecha no
  prevista, agrega una validacion enfocada y vuelve a ejecutar esa variable.
- Los resultados anteriores pueden aportar contexto de fuente, pero no son
  evidencia del score actual sin revalidar claim, poblacion, grain, ventana y
  regla de aceptacion.
- El motor y la metodologia son genericos. Los catalogos concretos de variables
  son configuracion de una ejecucion y no deben codificarse dentro del skill.

## Assessment

- Specs nuevas o regeneradas: version 4.
- El spec v2 de 43 variables y los workbooks/profile v2-v3 son referencia historica, no
  evidencia suficiente para una nueva ejecución.
- Las explicaciones, comentarios y racionales del workbook se escriben en
  español. Los nombres canónicos de criterios, tablas, columnas y otros
  identificadores técnicos pueden permanecer en inglés.
- Mantén exactamente las hojas `Variable assessment`, `Coverage` y
  `Score rationale`.
- Cada 0/1 debe tener un comentario y una fila de rationale; cada 2 no debe
  tenerlos.
- Ejecuta pruebas y validadores de ambos skills después de cambiar reglas,
  scripts o contratos.

## Narrativa de los reportes

- Todo notebook, HTML, plan de análisis, evidencia explicada, limitación y
  acción recomendada debe estar en español, salvo el texto proyectado de los
  decks en inglés indicados en la sección de presentaciones.
- En slides y otros elementos visuales, todo número entero se muestra sin
  decimales y todo número no entero con un máximo de un decimal. Aplica a
  etiquetas, ejes, KPIs, tooltips y tablas; los cálculos y la evidencia pueden
  conservar la precisión necesaria.
- Cada variable debe comenzar con un resumen del flujo histórico y después
  explicar cada validación mediante: pregunta, motivo, método, regla de
  aceptación, métricas observadas, conclusión, impacto en score y acción.
- Los cruces con campos relacionados sólo se ejecutan cuando existe una
  hipótesis específica. La evidencia contextual no puede demostrar por sí
  sola la definición ni elevar un score.
