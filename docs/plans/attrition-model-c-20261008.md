# Modelo C sin QVoice: diseño congelado antes del entrenamiento

## Objetivo y comparación

Mejorar estimación R6, detección de grupos de riesgo e interpretación frente a la receta B.
Modo: `presentation`. No modifica B, B + QVoice ni la presentación. C + Q sólo será una etapa posterior si C mejora.
Se reutiliza la autorización de procesamiento en memoria del 1 de octubre de 2026.

## Selección

Los parámetros exactos están en `config/engineering_model_c_20261008.json`.
Toda variable de B puede retirarse. L1 logístico mensual es únicamente un filtro supervisado:
sus coeficientes no son el modelo final. Sus conjuntos se reajustan como hazard cloglog L2.
Se incluyen también el conjunto completo y B. Los padres de una interacción se conservan si ésta entra.
Las seis penalizaciones L1 generan un recorrido acotado; no se prueban las 2^21 combinaciones.
PCA es compatible con snapshots si se aprende sólo en el pasado, pero aquí no se usa: optimiza
variación de los predictores y dificulta mantener grupos comprensibles. L1 responde a la salida observada.

Cada origen externo contiene dos validaciones internas, 15 y 9 meses antes, de tres snapshots.
Los seis meses de seguimiento interno deben terminar antes del origen externo.
Cada entrenamiento mensual exige `label_end <= origen`; cada evaluación R6 exige seguimiento completo.
L1 y las categorías se aprenden con el entrenamiento interno más antiguo; la comparación interna elige
variables y L2. Después se reajusta sólo con el pasado y se mide en los seis snapshots externos siguientes.
Se evalúa retrospectivamente febrero 2024–enero 2026, con sus seguimientos hasta julio 2026.
No se describen estos años previamente explorados como un holdout virgen.

## Métricas y decisión

Selección por log-loss R6, sujeta a Brier no peor y ranking dentro de 1% de B en validación interna.
Se favorece el conjunto más pequeño dentro de 0,2% del mejor log-loss elegible.
La regla final exige mejora de al menos 0,5% en log-loss; Brier no peor;
PR-AUC y lift10 al menos 2% mejores y ganancias en tres de cuatro periodos;
error medio de grupos y error del grupo alto de C sin empeorar más de 0,1 puntos porcentuales.
Bootstrap por persona para diferencias de pérdidas, conservando la dependencia de snapshots;
no mide incertidumbre macrotemporal. Si el intervalo incluye cero, la mejora queda como indicativa.

## Grupos

Árbol de máximo tres condiciones y ocho hojas, entrenado para resumir el riesgo predicho en la
última foto anterior al origen; mínimo 300 personas por hoja de entrenamiento. Se congela antes
de ver salidas futuras. Variables originales, sin calendario en las reglas.
Grupo alto: hojas ordenadas por riesgo predicho en entrenamiento hasta cubrir al menos 20%.
Se reporta cobertura real porque una hoja completa puede superar ese porcentaje.
B y C se comparan en los mismos grupos de C; también se mide el ranking propio de cada modelo.
Publicación sólo con 30 personas por snapshot y 30 eventos para tasas observadas.

## Datos y alcance

Inventario trazable de las 43 variables más dos adiciones del playbook en
`config/engineering_model_c_inventory_20261008.json`. Las representaciones parciales y exclusiones
son explícitas; no se afirma haber probado cada concepto o combinación.
Las nuevas entradas tienen contratos y SQL agregados por variable. Se ejecutan y cierran secuencialmente.
No es un nuevo assessment v4 ni se asignan scores de disponibilidad o definición.
Comp ratio y capas son campos almacenados: no se afirma haber demostrado su fórmula ni raíz CEO.
Los vacíos de adquisición significan ausencia de registro, no origen orgánico.
Se conserva la última foto sin etiquetas para obtener grupos pronosticados, sin llamarlos observados.
Se exige primera foto de registro <= t para salidas del equipo y manager usadas como features.
Este endurecimiento se aplica a B y C en el mismo frame; el control reproduce la receta de B,
no promete reproducir exactamente sus cifras históricas. IOS carece de fecha de publicación por evento.

### Ajuste de disponibilidad previo al entrenamiento

La auditoría de transferencias del 8 de octubre encontró flag poblado pero cero eventos en
2020–2021; el primer evento registrado aparece el 23 de octubre de 2022. Esto no demuestra
que no hubiera transferencias antes. Se codifica «historia no confirmada» antes del 23 de
octubre de 2023, reservando doce meses de historia observada. La ausencia de eventos antiguos
sigue siendo una limitación de fuente. Evidencia: `engineering_model_c_transfer_history_20261008.sql`.
Como diagnóstico adicional, se comparan los árboles de B y C entrenados por separado y
congelados, ponderando empates para medir el ranking con la misma fracción de población.

## Eficiencia y trazabilidad

Una carga a memoria por lotes, matrices dispersas reutilizadas, predicción R6 analítica,
ninguna caché de personas en disco. Se guardan configuración congelada, hashes de consultas y código,
métricas por periodo, recorrido de selección, coeficientes, reglas y verificación sintética.
Se guarda el modelo final como candidato aunque no supere la regla, identificado como experimental.
