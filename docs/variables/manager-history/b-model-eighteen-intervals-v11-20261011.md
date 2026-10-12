# Contexto del manager a dieciocho intervalos

Modo `presentation`. El feed permite observar eventos Voluntary desde
23-oct-2022; las fechas efectivas anteriores no acreditan conocimiento
histórico. Por eso la primera ventana completa de dieciocho intervalos termina
en abril de 2024. La población de exposición es Employee, Regular, activa y
sin RF360; la asignación persona-foto final se restringe a Engineering.

Pregunta: ¿se reproduce el indicador del V11 con información conocida en cada
foto? Motivo: distinguir persistencia de salidas del equipo de una ventana
reciente de seis meses. Se atribuye cada salida al equipo al inicio del
intervalo y sólo se cuenta después de su primera observación, sin conflictos
de tipo ya conocidos. Se exige continuidad, equipo medio de al menos cuatro
personas, dos salidas y tasa de al menos 1.3 veces el benchmark ponderado.

La revisión v2 detectó una diferencia en el control independiente del
benchmark: dividir exposiciones por 18.0 introducía redondeo decimal. Una
auditoría separada confirmó el benchmark principal por suma de exposiciones y
por pesos de doble precisión. La revisión v3 corrige sólo el control; mantiene
la feature, el benchmark principal y la tolerancia de 1e-8.

Resultado: las siete consultas anuales de v3 pasaron con cero duplicados,
contradicciones, atribuciones múltiples, eventos futuros, violaciones de
historia o umbral y diferencias de fórmula. Hay 21,887 persona-fotos observables
en 2024, 35,846 en 2025 y 24,295 en 2026. El indicador está por encima del
benchmark en 4,428, 7,220 y 5,034 persona-fotos, respectivamente. Son métricas
de preparación; todavía no miden ganancia predictiva.

Conclusión y acción: probar `manager_above_average18` como B + X manteniendo
los periodos sin ventana completa y los equipos no elegibles como desconocidos.
La observabilidad es limitada por diseño. No representa causalidad ni evaluación
individual del manager. Impacto en score: ninguno.

SQL activo:
`queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v3.sql`.
Evidencia y fecha de cada consulta:
`output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-manager18-v3.json`.
Diagnóstico numérico:
`output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-manager-benchmark-precision.json`.
Los años 2020–2023 se reutilizaron con SQL idéntico y fecha original; 2024–2026
se ejecutaron con el control corregido. v2 no habilita la preparación.
