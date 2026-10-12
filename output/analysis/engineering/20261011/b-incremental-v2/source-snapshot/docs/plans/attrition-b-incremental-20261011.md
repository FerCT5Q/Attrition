# B como base obligatoria: incorporaciones individuales y combinaciones pequeñas

Fecha: 11-oct-2026. Entregable `presentation`. Experimento retrospectivo, sin
promoción automática ni cambios a B, C o CQ publicados.

## Pregunta y alcance autorizado

El usuario pide conservar todas las variables de B, probar cada incorporación
por separado y construir una extensión pequeña con RH y QVoice. También pide
incluir las variables pendientes del inventario que podamos preparar con las
fuentes disponibles. Los 43 conceptos del inventario no equivalen a 43
predictores independientes: varios comparten una representación y otros no
tienen una fuente histórica utilizable.

B conserva diez términos: `level_grouped`, `tenure_playbook_band`,
`calendar_month`, `manager_changes_12m`, `team_exits_12m`,
`direct_reports_band`, `time_since_promotion_band`, `rehire`,
`level_x_tenure` y `tenure_x_manager_changes`. Se pueden reajustar sus
coeficientes con datos anteriores al corte; ninguna selección puede eliminar
un término. Se conserva el modelo mensual cloglog y su fórmula de riesgo a
seis meses.

## Preparación de entradas

Se utiliza `attrition-redshift-db` y el ciclo de evidencia de
`evaluate-attrition-variable`. Este trabajo valida entradas de un experimento;
no produce nuevos scores de assessment. La autorización de procesamiento en
RAM es `config/attrition_model_in_memory_training_authorization_20261001.json`.

Primero se consulta exclusivamente metadata. Después se termina la evidencia
de cada concepto antes de pasar al siguiente. Cada ficha declara concepto,
uso, fecha de conocimiento, población, grain, tipo semántico, consulta,
regla de aceptación, resultado, limitación y acción. Los resultados anteriores
se usan como contexto y se conservan sus hashes; no se copian como evidencia
de una nueva comprobación.

Población: Employee, Regular, activo, Engineering, excluyendo RF360, en cada
foto mensual. Historia objetivo desde 26-jul-2020; conocimiento hasta
7-sep-2026. Grain interno persona-snapshot. Sólo se guardan parámetros y
agregados, nunca filas, llaves, scores individuales ni compensación exacta.

Las candidatas iniciales son las once incorporaciones de C y las siete de
historia reciente de D. Se exploran además, por orden de dependencia:

| Concepto pendiente | Representación que se comprobará | Regla y límites previos |
|---|---|---|
| Familia de puesto | Familia y grupo registrados en la foto | Un valor no contradictorio por persona-foto; no inferir equivalencia entre detalle y grupo |
| Ubicación laboral | País y sitio de trabajo registrados | Historia suficiente; sin domicilio personal ni coordenadas individuales |
| Grado de compensación | Código registrado, con categorías infrecuentes agrupadas | No equivale a salario ni a nivel; sin valores de pago individuales |
| Ubicación respecto al manager | Coincidencia de sitio/ciudad/país en la misma foto | Join histórico 0/1, sin elegir silenciosamente entre managers o ubicaciones incompatibles |
| Posición salarial dentro del equipo | Banda de posición relativa dentro de un grupo comparable | Cálculo dentro de SQL; misma moneda y nivel, denominador suficiente; no extraer importes |
| Entrada por promoción o contratación | Evento anterior y compatible con episodio y grado actual | Historia incompleta debe distinguirse de ausencia de promoción |
| Tiempo en puesto | Fecha registrada de entrada al perfil, con bandas | No interpretar el nombre como fórmula validada; respetar inicio de fuente |
| Talent index | Sólo si metadata y definición permiten una entrada histórica interpretable | No inventar fórmula, dominio ni fecha de conocimiento |
| Applications y fuentes externas | Revisar limitaciones ya documentadas y metadata disponible | No incorporar fuentes sin enlace y fecha de conocimiento defendibles |
| QVoice | 33 preguntas comunes, Career y promedio; controles de disponibilidad y posible normalización regional | Wave 2024 en 2025, wave 2025 en 2026; continuidad de episodio; sin wave 2026 en esta evaluación |

Se documenta cada exclusión. Género y otros atributos protegidos, identidades
de líderes, texto libre y domicilios permanecen fuera de los predictores.
«Capas» conserva el significado de valor almacenado, no distancia al CEO;
compa-ratio conserva el significado de razón almacenada, no fórmula validada.
Career mantiene la advertencia sobre cambio de redacción entre waves.

## Comparación temporal

Se fijarán en la configuración las entradas admitidas y sus contratos antes
de entrenar. Las cinco ventanas externas previstas para RH comienzan en
feb-2024, ago-2024, feb-2025, ago-2025 y ene-2026. Las primeras tres tienen seis
fotos, la cuarta cinco y la última dos. Ningún resultado externo selecciona
variables, penalización ni tamaño de modelo.

Para cada corte se reserva internamente una ventana de tres fotos con riesgo
a seis meses ya maduro. El ajuste interno sólo usa etiquetas mensuales
finalizadas antes de la primera foto reservada. Se elige la penalización de B
en esa validación y se mantiene igual al comparar `B + X`; así la diferencia
principal es la incorporación. Se comparan todas las candidatas individuales.
Luego se prueban todos los pares y tríos entre las seis mejores candidatas de
la validación interna, incluso cuando una incorporación sola no pase la
regla de adopción. No se afirma búsqueda exhaustiva de todos los predictores
posibles. La selección siempre puede volver a B.

La selección usa pérdida logarítmica a seis meses, con Brier y capacidad de
ordenar el riesgo como controles, y prefiere menos variables cuando la
diferencia es pequeña. El error por grupo y la captura se informan en las
mismas particiones. Las tolerancias exactas quedan congeladas en config
antes del ajuste. No se exige incorporar dos o tres variables si no ayudan.

QVoice se incorpora mediante una corrección de riesgo sobre B y sobre la
extensión de RH elegida sólo con pasado. Se compara cada pregunta contra el
mismo modelo sin pregunta y contra una actualización de intercepto. Después
se prueban pares y tríos de las seis mejores. Se incluye un control de
disponibilidad para distinguir contenido de encuesta de falta de respuesta.
Cuando no existe historia para validar seis meses sin solapar entrenamiento,
se usa una reserva mensual explícita y se declara esa limitación. QVoice se
evalúa externamente en ago-dic-2025 y ene-feb-2026, con poblaciones idénticas
entre alternativas. Los aliases de una misma pregunta se cuentan una vez.

## Grupos, resultados y verificación

Los grupos se mantienen en antigüedad × salidas previas del equipo × nivel.
La elegibilidad exige 300 personas por foto. Se informa captura al cubrir
20%, 30% y 40% de población, Brier, pérdida logarítmica, PR-AUC y error de
estimación de los mismos grupos. Se añade precisión sobre la selección de B
para evitar atribuir a precisión un cambio de población seleccionada.

Los intervalos pareados remuestrean personas completas únicamente en RAM.
Se informa cada periodo y el promedio con igual peso por periodo. Los años
ya explorados siguen siendo retrospectivos: una búsqueda más amplia no
convierte estos datos en confirmación prospectiva.

Las pruebas verifican que B sea obligatorio, que la selección no reciba
resultados externos, la separación temporal, el tratamiento de categorías
infrecuentes aprendido sólo en entrenamiento, la equivalencia del ajuste
comprimido y la reproducción del artefacto exportado. Se registran fallos de
convergencia y se validan las reglas de privacidad. Los modelos anteriores
se comparan por hash antes y después.

Salida vigente: `output/analysis/engineering/20261011/b-incremental-v2/`, con
config congelada, ledger de entradas, inventario de inclusión/exclusión,
resultados por candidata y periodo, decisiones de selección, modelos
experimentales, informe en español, gráficos agregados y manifest.

## Repetición por integridad de exportación

El intento v1 se detuvo al comprobar el segundo periodo: las columnas del
encoder exportado seguían el orden del catálogo, pero la lista de variables
seguía el orden de selección. Esa diferencia podía desalinear coeficientes
al cargar combinaciones. Se conserva v1 con estado fallido y copia de sus
fuentes; no es una ejecución final válida.

La v2 alinea ambos órdenes en RH y QVoice. Dos pruebas con datos sintéticos
reproducen el fallo anterior y comprueban su corrección. No cambia ninguna
variable, periodo, umbral, regla de selección o cálculo estadístico. Se
reutiliza la evidencia agregada de las entradas de este mismo experimento,
con sus fechas, SQL y hashes originales: claim, población, grain y ventana
son idénticos. Las filas se vuelven a consultar sólo en RAM, con nuevas
llaves efímeras y una nueva reconciliación de población y joins. Esta
repetición técnica no crea ni modifica scores de assessment.
