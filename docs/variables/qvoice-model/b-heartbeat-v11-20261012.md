# Heartbeat V11: posibilidad de reconstrucción antes del corte

Modo `presentation`. El V11 define el signo de cada respuesta ordinal frente
al promedio personal de 53 preguntas, con al menos 38 respuestas válidas.
El reporte de 2026 eligió preguntas destacadas descriptivamente; esa selección
no se traslada al experimento predictivo. La equivalencia de preguntas entre
waves debe verificarse antes de intentar reconstruir signos.

Concepto y uso previos: señal relativa de encuesta, tipo `survey` con
transformación derivada, potencial incorporación a B. Grain persona-wave y
luego persona-foto Engineering, Employee, Regular, activo y sin RF360.
Frontera 7-sep-2026 y política anual obligatoria: 2024→2025, 2025→2026,
2026→2027. Los valores binarios favorables no permiten recuperar una escala
1–5. No mezclar respuestas de waves distintas.

Pregunta: ¿cada wave 2024/2025 contiene exactamente los 53 ítems ordinales del
diccionario V11, con un encabezado único por ítem? Método: inspección fresca
de hojas, encabezados y hashes, comparación exacta con el diccionario; no se
leen respuestas en esta comprobación. Regla necesaria: 53 coincidencias
únicas en cada wave. Si faltan ítems o hay ambigüedad, el Heartbeat exacto no
se habilita, sin sustituir su denominador ni copiar el ranking de 2026.
Si pasa, haría falta verificar valores, mínimo de respuestas, signos
recalculados y enlace temporal antes de probarlo. Impacto en score: ninguno.

## Resultado al 12-oct-2026

La inspección ejecutada con `tools/audit_b_v11_heartbeat.py` conserva hashes
de archivos y diccionario en
`output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-heartbeat-headers.json`.
2024 tiene cero columnas ordinales reconocidas. 2025 tiene 52 coincidencias
ordinales únicas; falta **Q42**. No hay ambigüedades de encabezado. La regla
de 53 ítems no pasa en ninguna de las dos waves.

Conclusión: las escalas de 2025 existen, pero no permiten transportar la
definición exacta V11 ni entrenarla en 2024 bajo el desfase anual acordado.
No sustituir 53 por 52 ni imputar respuestas ordinales desde los binarios.
Heartbeat queda fuera de esta ronda; las 33 preguntas binarias comunes y
los otros indicadores QVoice preparados siguen disponibles para B + X.
Acción: recuperar las escalas originales completas o definir y validar una
medida alternativa con historia propia. Los datos de 2026 corresponden a
predicciones de 2027. Sin cambios de score.
