# Annual Review del V11 en la comparación con B

Modo `presentation`. La lámina del playbook describe promoción registrada en
AR25 por track del ciclo. B ya contiene tiempo desde promoción, calculado con
eventos `is_promo`; ambas representaciones no son equivalentes. La preparación
de entrada al grado y track ya está cerrada en esta ronda.

Antes de consultar: la candidata sería el flag `promotion_yes_no` del último
ciclo de Annual Review disponible a la fecha de predicción. Tipo semántico:
evento de encuesta/revisión por persona-ciclo, trasladado a persona-foto. Uso:
examinar aporte incremental de una promoción de ciclo, con B obligatorio.
Población objetivo: Engineering, Employee, Regular, activo y sin RF360 entre
26-jul-2020 y 7-sep-2026. No usar la tasa de promoción por track calculada con
eventos futuros ni tratar `No` como ausencia de toda promoción.

Pregunta: ¿hay ciclos fechados antes del corte, con grain único y fecha de
disponibilidad verificable? Método: auditar ciclos, duplicados, dominio del
flag, rangos de carga/modificación y enlace agregado a la población. Regla
previa necesaria: cero conflictos o flags inválidos y al menos un ciclo con
registros cargados y modificados antes del corte. Aun si pasa, hace falta
fecha oficial de publicación o historia as-of; el nombre AR25 no la prueba.
Si la condición necesaria falla, mantener las otras representaciones de
promoción y documentar esta diferencia. Impacto en score: ninguno.

## Resultado

`queries/audits/engineering_b_v11_annual_review_history_20261012.sql` pasó el
requisito técnico el 12-oct-2026. La evidencia
`output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-annual-review-history.json`
conserva fecha, hashes y métricas: seis ciclos AR20–AR25; cero duplicados,
conflictos, llaves faltantes o flags inválidos. AR25 tiene 44,426 participantes,
33,048 vinculados a personas alguna vez elegibles para Engineering.

La carga y modificación de AR20–AR24 es exactamente 25-jun-2025; para AR25,
9-nov-2025. Estos timestamps anteriores al corte permiten investigar la
fuente, pero no reconstruyen la publicación original de cada ciclo en
2020–2024. El único historial disponible es una fila actual por persona-ciclo;
no se verificó un calendario de disponibilidad de decisiones ni versiones
históricas. Por ello el resultado técnico `pass` **no habilita** trasladar
AR20 al año 2020 ni AR25 al inicio de 2025.

Decisión: no añadir el flag de Annual Review a la selección de esta ronda.
Conservar la promoción de B, la entrada observada al grado y el track como
representaciones distintas. Acción: obtener calendario oficial de publicación
y cambios del ciclo, o diseñar una comparación posterior que use únicamente
las cargas observadas con seguimiento suficiente. Sin impacto en scores.
