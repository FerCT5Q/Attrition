# B frente a C: priorizar grupos donde se actuaría

## Decisión y alcance

El usuario aprobó dar prioridad a grupos de riesgo alto y parte del medio,
manteniendo bajo riesgo en entrenamiento y seguimiento. Esta ejecución aplica
ese enfoque a B y C ya seleccionados; compara su utilidad retrospectiva para
decidir dónde enfocar una intervención. No selecciona variables nuevas.

Modo: `presentation`. Población: Engineering, Employee, Regular, activo, sin
RF360. Resultado: salida voluntaria durante los seis meses siguientes a cada
snapshot. Unidad: persona-snapshot, con ventanas que pueden solaparse.
Frontera de conocimiento: 7 de septiembre de 2026.

## Método congelado antes del cálculo

1. Reutilizar los cuatro C guardados de `model-c-v2`; reconstruir únicamente B
   con sus variables y L2 archivados. Usar la misma consulta guardada y las
   mismas fechas. Comprobar reproducción de métricas y población antes de
   interpretar resultados adicionales. Una discrepancia suspende el cálculo
   de ese periodo y requiere investigar cambios de fuente o implementación.
2. Conservar las reglas de C. Reconstruir las reglas de B con su receta y
   semilla originales. Sólo el riesgo predicho en entrenamiento determina el
   orden de prioridad; ninguna salida futura determina reglas ni asignación.
3. Comparar capacidades de 20%, 30% y 40% en cada snapshot. El escenario
   central es 30%; su elección precede los resultados. Estas proporciones son
   hipótesis para comparar, no capacidad operativa confirmada.
4. Usar ponderación fraccional en la hoja que cruza el límite, igual para todos
   sus integrantes. Es el rendimiento esperado si se elige aleatoriamente
   dentro de esa hoja; no una selección individual publicada ni una regla
   para tratar obligatoriamente sólo parte de un grupo. Informar también las
   coberturas de hojas completas inmediatamente inferior y superior.
5. Métricas: captura de salidas, attrition observado y estimado, error absoluto
   agregado, error absoluto medio ponderado de cada hoja seleccionada y de
   cada hoja-snapshot, peor error de una hoja publicable, y ampliación desde
   20% al 30%/40%. El error de hojas individuales se calcula antes de promediar
   para evitar compensar subestimaciones con sobreestimaciones.
6. Comparar ambos estimadores también en las mismas hojas seleccionadas por
   cada modelo. Separar calidad de selección y calidad de estimación.
7. Documentar claridad (máximo 3 condiciones y 8 hojas) y coincidencia de las
   asignaciones ponderadas de prioridad al reajustar, sobre la misma población
   del primer snapshot del periodo siguiente. No confundir estabilidad de
   reglas con estabilidad de las salidas.
8. Calcular IC95 pareado para diferencia de captura por bootstrap de personas,
   conservando juntas todas sus ventanas y dando igual peso a los cuatro
   periodos. Modelos, reglas y asignaciones permanecen fijos; no incorpora
   incertidumbre de entrenamiento ni eficacia de la intervención.
9. Usar ranking individual sólo como diagnóstico de la pérdida de señal al
   resumir en reglas. Exportar únicamente sus métricas agregadas.
10. Añadir por separado el snapshot 22-feb-2026, con seguimiento hasta
    22-ago-2026 y los modelos/reglas del corte 1-ago-2025. Es una extensión
    retrospectiva de un snapshot, no un periodo independiente de seis fotos
    ni un holdout virgen: la historia ya fue explorada en otros análisis.

## Interpretación y controles

La regla de preferencia por escenario queda en el JSON de configuración. El
30% se fija como escenario central sin escoger después el escenario favorable.
No se asume causalidad: capturar salidas no significa que todas sean evitables
ni estima cuántas evitaría una acción. El efecto y costo de la intervención no
están disponibles.

Sólo se procesan filas y llaves efímeras en RAM bajo
`config/attrition_model_in_memory_training_authorization_20261001.json`.
No se persisten filas, llaves, puntuaciones individuales, salarios exactos ni
texto libre. Cohortes mínimas: 30 personas por foto; tasas de hojas sólo con
30 personas distintas con salida. Las métricas agregadas de error pueden usar
internamente todas las hojas; el peor grupo publicado sólo incluye hojas con
tasas publicables y se identifica cualquier cobertura suprimida.

Los resultados se guardan en una carpeta nueva; B, C y sus evaluaciones previas
conservan su trazabilidad. No hay una reevaluación de scores de variables ni
nuevo entrenamiento de C. La comparación requiere cuatro ajustes B, evitando
repetir la selección anidada completa.

## Entrega y revisión

Informe en español con tabla principal, gráfico de captura frente a capacidad,
desglose temporal, errores por grupo prioritario, escenarios de hojas completas,
extensión de febrero y manifiesto de fuentes. Verificar identidades matemáticas
de captura/lift, misma capacidad, etiquetas maduras, reproducción de la
evaluación original y umbrales de publicación como parte del cálculo.
