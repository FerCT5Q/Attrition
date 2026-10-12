# C + QVoice: comparación posterior a la elección de C con los cortes de B

Plan previo al cálculo, 8-oct-2026. Modo `presentation`.

## Pregunta y decisión

¿Las respuestas QVoice mejoran las estimaciones y la identificación de grupos
prioritarios del C elegido? Se mantiene la agrupación antigüedad × salidas del
equipo × nivel. Capacidad principal 30%; sensibilidades 20% y 40%.
Se conserva C como control y se archiva una extensión independiente.

Hipótesis: las percepciones de permanencia, carrera y entorno laboral añaden
información a las características ya utilizadas por C. Una ganancia en ranking
individual podría no trasladarse a los grupos fijos; se medirán ambos niveles.

## Alcance de fuentes y contrato

Se reutilizan las definiciones, codificadores, fuentes, encabezados exactos y
exclusiones ya empleados en B+QVoice. No es un nuevo assessment ni asigna
scores. Los contratos y límites previos se conservan y se verifican hashes de
fuentes. Skills: `attrition-redshift-db`, criterios de evidencia de
`evaluate-attrition-variable` y narrativa `morgan-vis`.

- Población: Engineering, Employee, Regular, activo, sin RF360.
- Outcome: salida voluntaria; ajuste con intervalos mensuales completos y
  evaluación R6. Grain persona-snapshot exclusivamente en RAM.
- Autorización existente: `config/attrition_model_in_memory_training_authorization_20261001.json`.
- Encuesta anual: wave 2024 sólo para fotos 2025; wave 2025 sólo para fotos
  2026. Regla de negocio aprobada, no fecha observada de publicación.
- Respuesta utilizable sólo con episodio laboral continuo desde el ancla de
  encuesta. Llaves duplicadas se excluyen; no respuesta, ausencia de pregunta
  y episodio diferente conservan estados distintos.
- Semántica: respuestas binarias de encuesta; el promedio de 33 preguntas es
  una derivación con componentes y bandas congelados. Career conserva la
  diferencia de redacción de 2024 como limitación exploratoria.
- Q6/Q9 no tienen historia común suficiente; Heartbeat, comentarios y wave
  2026 quedan fuera. No se extraen valores de compensación exacta.
- Query nueva: `queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql`.
  Copia exacta de la query de C, añadiendo sólo los indicadores de continuidad
  de episodio ya usados para QVoice. La comprobación previa debe confirmar que
  al remover esa proyección se recupera la consulta original byte por byte.
- Reglas de aceptación: población mensual idéntica a C; una fila por
  persona-snapshot; etiquetas binarias y maduras; reproducción de métricas C
  del último fold; wave = año de snapshot menos uno; columnas y estados en
  listas permitidas. Publicar contratos comprobados con agregados, sin nuevos scores.

## Diseño temporal y selección

Evaluar agosto–diciembre de 2025 (cinco fotos) y enero–febrero de 2026 (dos),
como en B+QVoice. Son periodos retrospectivos ya explorados, no dos muestras
independientes: se repiten personas y algunas ventanas de seguimiento.

1. Restaurar el C archivado más reciente disponible antes de cada origen.
   Para ambas evaluaciones externas corresponde al origen 1-ago-2025.
   No reajustar C ni cambiar sus coeficientes.
2. En cada corte QVoice, reservar los dos últimos intervalos mensuales
   completos para selección. La corrección candidata se ajusta en los anteriores.
   El C usado para seleccionar será el último archivado antes del comienzo
   de selección, evitando un offset ajustado con sus etiquetas reservadas.
3. Buscar los 255 subconjuntos de ocho bloques: Q4, Q12, Career, promedio de
   33 preguntas, Engagement, Connection, Wellbeing y Confidence. Añadir cinco
   tamaños PCA de los 33 ítems sólo como diagnóstico. Reutilizar matrices.
   Penalizaciones 0.1, 1 y 10; criterio Brier mensual, como en B+QVoice.
4. Reajustar sólo la corrección elegida con todas las etiquetas mensuales
   maduras anteriores al origen, usando C como offset. Esta versión sin
   calibración posterior es el candidato principal declarado.
5. Ajustar también un intercepto mensual y un control que utiliza sólo los
   estados de disponibilidad de las preguntas seleccionadas. Permiten distinguir
   el aporte de respuestas de una actualización de tasa o de participación.
6. Evaluar sin cambiar la selección con resultados externos. El modelo final
   al corte 7-sep-2026 se selecciona de nuevo con meses anteriores; sus
   coeficientes finales no se presentan como si ya hubieran sido evaluados.

## Calibración adicional

Comparar identidad y escalar R6: `1 - (1 - R6)^exp(a)`. El escalar se ajusta
con etiquetas de seis meses maduras al corte. Las predicciones de calibración
proceden de correcciones auxiliares entrenadas antes de cada foto y del C
archivado disponible en ese origen. Usar hasta seis fotos y exigir al menos
tres; con menos, identidad. Aplicar el mismo procedimiento a C y controles.

Las columnas y penalización elegidas al corte se reutilizan en los auxiliares:
la selección es retrospectiva respecto a esas fotos. Se declara esta limitación;
ninguna salida de los periodos externos participa en su calibración. No repetir
la antigua calibración mensual de pendiente e intercepto que dio problemas en B.
Un escalar preserva el ranking individual, pero puede cambiar el orden de medias
de grupos; se comprobará y medirá la asignación efectiva, sin asumir igualdad.

## Métricas y veredicto

R6 global: log-loss, Brier, PR-AUC, lift, estimado/observado y error agregado.
Grupos: captura al 20/30/40%, error por grupo y grupo-snapshot, peor error
publicable, observado/estimado, número de grupos y resto. Ordenar por riesgo
medio vigente y aplicar capacidad igual por snapshot, con pesos uniformes en
el grupo del límite. Mostrar también alternativas con grupos completos.

Promedio de periodos con igual peso. Bootstrap pareado por persona conservando
todas sus ventanas, 500 réplicas; intervalos puntuales condicionales a ajustes y
selección. Evidencia favorable principal si captura mejora en ambos periodos,
su IC95 medio es positivo, errores por grupo y grupo-snapshot no empeoran más
de 0.1 pp, pérdidas globales no empeoran más de 0.5% relativo y las respuestas
aportan frente al control de disponibilidad. Separar ganancia predictiva,
calibración y utilidad de agrupación; no declarar sustitución automática.

## Eficiencia, conservación y entregables

Cargar sólo fotos 2025–2026, en lotes anuales; ocho modelos C/B previos no se
reentrenan. Leer cada wave una vez; precalcular matrices y offsets y reutilizar
auxiliares por origen/especificación. Registrar tiempos y convergencia.

Nueva carpeta `output/analysis/engineering/20261008/model-c-plus-qvoice-v1/`:
configuración, fuentes congeladas, selección por corte, modelos, calibradores,
evidencia agregada, comparaciones, informe y gráfico en español. Hashes de los
artefactos B, B+QVoice y C antes/después. Sólo conteos agregados seguros;
tasas por grupo con mínimo 30 personas por foto y 30 personas con evento.
Comprobaciones del cálculo y de conservación integradas; no se añaden suites.
