# C + BU L3 sin QVoice y corrección del deck

Modo `presentation`. Solicitud: comprobar si C + BU L3 es mejor y conservar
las nueve diapositivas del deck de evolución del 12-oct a las 08:33.

La ronda BU v7 ajustó C + BU como base de C + BU + QVoice, pero no publicó
su evaluación sin QVoice ni guardó los coeficientes. Se necesitan dos ajustes
RH para recuperar esa comparación. Se añaden dos controles C con la misma
fecha de ajuste y dos correcciones QVoice sobre C + BU para distinguir el
aporte de BU y el de encuesta. No se buscarán variables ni penalizaciones.

## Definición previa y aceptación

BU L3 es un mapping histórico (`grouped_mapping`) desde centro de costo a
`d_department.ude_bu_reporting_l3`, vigente en la foto RH. Se conserva la
codificación y pooling de v7: categorías con al menos 300 personas distintas
de entrenamiento; resto a `(other)`, ausencia a `(unknown)`. El uso es predictor
categórico, no un cambio de los grupos de reporte. Se reejecuta la auditoría
as-of guardada: cero duplicados o múltiples matches; máximo 0.1% sin match.
No se asignan ni elevan scores de assessment.

Engineering, Employee, Regular, activo, sin RF360. Grain persona-mes sólo en
RAM; salida voluntaria a seis meses. Evaluación agosto–diciembre 2025 y
enero–febrero 2026, mitad del peso por periodo. Entrenamiento: sólo etiquetas
maduras al 1-ago-2025 o 1-ene-2026. Mismos grupos de antigüedad × salidas del
equipo × nivel, mínimo 300, capacidades exactas 10/20/30 y límites con grupos
completos. `job_family_detail` excluida.

Comparaciones: C histórico, C reajustado, C + BU, CQ, C + BU + QVoice, FQ,
FQ + BU. El contraste BU frente a C reajustado aísla la incorporación bajo
igual corte y estructura; CQ conserva la base de agosto también en enero.
500 remuestreos por persona compartidos entre modelos y periodos; intervalos
95% de pérdidas, captura, error y sesgo. No son intervalos individuales.

Se exige reproducir CQ/FQ/FQ+BU archivados con tolerancia 1e-8, conservar
población y capacidad y reproducir modelos tras serializarlos. Para responder
«mejor» se separarán pérdidas predictivas, captura y error por grupo; una
captura empatada no descarta una mejora de estimación. La elección vigente CQ
no cambia por la ejecución. IOS y publicación real QVoice siguen sin fecha
histórica acreditada; la conclusión permanece retrospectiva.

## Presentación

Se parte de `20261012-0833_evolucion-b-cq-error-vs-c/presentacion-eng.html`.
Se mantienen nueve slides, inglés, cuatro temas y controles. Se actualizarán
comparación, cobertura, capacidad, calibración y lectura RH dentro de esos
nueve espacios. Fichas completas, tabla de 44 variables y diagnósticos siguen
en el paquete de revisión de Julia; no se añaden slides de anexo.
