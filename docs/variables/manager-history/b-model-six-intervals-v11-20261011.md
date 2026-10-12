# Contexto histórico del manager a seis intervalos

Modo `presentation`. Se asignan eventos Voluntary estrictos al equipo de
inicio del intervalo que contiene cada salida. Sólo entran al cálculo cuando
su primera observación no supera la foto objetivo y no existe un conflicto
de tipo ya conocido. La exposición y el benchmark son de empleados regulares
activos sin RF360; la asignación final es Engineering.

La primera observación de eventos en esta fuente es 23-oct-2022, aunque hay
fechas efectivas desde 2018. La auditoría del feed encontró 10,530 eventos
con registro más de 45 días después de la fecha efectiva. Por tanto, los seis
intervalos se consideran completos sólo desde abril de 2023. Antes se usa
historia no confirmada, también para el conteo de salidas.

Pregunta: ¿pueden probarse las salidas del equipo histórico y el ratio
observado/esperado del V11? Motivo: difieren de contar antiguos compañeros
del equipo actual. El esperado se estratifica por intervalo, región, familia,
nivel y antigüedad; estratos con menos de 30 exposiciones usan la tasa global.
Un prior de 60 exposiciones suaviza el ratio hacia uno.

Regla: cero duplicados, conflictos, atribuciones múltiples, eventos futuros,
ceros anteriores al feed y diferencias frente a la identidad algebraica
independiente del ratio. Las siete consultas anuales pasaron. En 2026 hay
ratio observable en 286,338 de 288,586 persona-fotos (99.2%).

Diez casos sintéticos del filtro SQL real también pasaron: eventos aún no
conocidos, intervalos futuros/antiguos y conflictos de tipo se excluyen según
su fecha. El fixture integral grande se interrumpió por su coste de ejecución;
no aporta un resultado de prueba. La validación efectiva consta en
`v11-manager-gate-synthetic.json`.

Conclusión y acción: probar ratio O/E y conteo `0 / 1 / 2+` por separado. No son
causalidad ni evaluación de un manager. No se publica su identidad. Impacto
en score: ninguno. SQL activo:
`queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v3.sql`.
Evidencia fechada en
`output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-manager6-v2.json`
y `v11-manager-feed.json`. La revisión anterior queda sustituida al haber
faltado el tratamiento explícito del inicio del feed.
