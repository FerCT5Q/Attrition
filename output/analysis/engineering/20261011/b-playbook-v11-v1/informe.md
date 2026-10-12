# B completo como base: qué aportan las incorporaciones

Modo `presentation`. Ejecución `engineering-b-playbook-v11-20261012-v1`; datos conocidos hasta 2026-09-07.

Se conservaron los **ocho predictores y las dos interacciones de B**. Se examinaron **41 incorporaciones de RH** y **51 señales de QVoice**, una por una. Dentro de cada corte se evaluaron también todos los pares y tríos de una lista de seis elegida sólo con datos pasados.

Los grupos permanecen en antigüedad × salidas previas del equipo × nivel. La captura se mide al priorizar grupos que cubren el 30% de las personas; cada grupo elegible tiene al menos 300 personas por foto.

## Selección final experimental

Incorporaciones de RH: Familia de puesto detallada, Ciudad laboral, Aproximación postal a oficinas de la ciudad (Onsite).

- Sobre B: QVoice: permanecer en Qualcomm (Q4), QVoice: poca intención de buscar otro empleo (Q12); ajuste `q`.
- Sobre B_RH: QVoice: permanecer en Qualcomm (Q4), QVoice: poca intención de buscar otro empleo (Q12); ajuste `q`.

Corte final: 2026-09-07. Los coeficientes finales no se usaron para simular resultados externos anteriores. No se sustituyó ningún modelo publicado.

## Resultado temporal de la regla de selección

Las cifras de cada alternativa corresponden al proceso que selecciona sólo con pasado. Las variables elegidas pueden cambiar entre periodos.

| Ventana | Alternativa | Salidas captadas (%) | Brier × 1000 | Error de los mismos grupos (pp) |
|---|---|---:|---:|---:|
| RH · 5 periodos | B | 44.6 | 29.8 | 0.7 |
| RH · 5 periodos | B_RH | 45.1 | 29.7 | 0.6 |
| QVoice · 2 periodos | B | 41.6 | 30.7 | 0.6 |
| QVoice · 2 periodos | B_RH | 42 | 30.6 | 0.6 |
| QVoice · 2 periodos | B_refresh | 41.6 | 30.7 | 0.6 |
| QVoice · 2 periodos | B_RH_refresh | 42 | 30.6 | 0.6 |
| QVoice · 2 periodos | B_Q | 41.6 | 30.6 | 0.6 |
| QVoice · 2 periodos | B_RH_Q | 42.8 | 30.6 | 0.6 |

RH usa cinco ventanas de feb-2024 a feb-2026. QVoice usa ago-dic-2025 y ene-feb-2026. Comparar alternativas dentro de la misma ventana de esta tabla. Brier y error de grupos: menor es mejor.

Los controles `refresh` sólo actualizan el intercepto. Cada pregunta tiene además un control con sus mismos estados de disponibilidad, para distinguir contenido de encuesta de calibración y ausencia de respuesta.

## Variables individuales

Las tablas sólo promedian los periodos con historia suficiente en entrenamiento y comparan cada incorporación contra su base en esos mismos periodos. Los resultados de una y cinco ventanas no son equivalentes. Las tablas individuales son exploratorias; la selección final se hizo dentro de cada corte.

La fuente de alcance es el **playbook V11 de 43 variables**, identificado por su hash en la configuración. Sus vistas se cruzan una por una con las representaciones y limitaciones de esta ejecución.

## Selecciones por periodo

| Periodo | Incorporaciones RH | QVoice sobre B | Grupos elegibles de B por foto |
|---|---|---|---:|
| feb_jul_2024 | Tiempo en nivel, Ciudad laboral, Familia de puesto detallada | Fuera de ventana QVoice | 19–20 |
| aug_jan_2024 | Familia de puesto detallada, Ciudad laboral, Experiencia previa | Fuera de ventana QVoice | 19–21 |
| feb_jul_2025 | Ciudad laboral, Familia de puesto detallada, Salidas observadas/esperadas del manager, 6 intervalos | Fuera de ventana QVoice | 21 |
| aug_dec_2025 | Ciudad laboral, Familia de puesto detallada, Salidas observadas/esperadas del manager, 6 intervalos | QVoice: permanecer en Qualcomm (Q4), QVoice: recomendar Qualcomm (Q1) | 19–20 |
| jan_feb_2026 | Familia de puesto detallada, Sitio laboral, Capa organizacional registrada | QVoice: permanecer en Qualcomm (Q4), QVoice: poca intención de buscar otro empleo (Q12) | 20 |

Se mantienen las dimensiones de los grupos de B para medir el efecto de las variables. El número de grupos elegibles se recalcula por foto; no se fuerza a 22. Esta comparación no busca un óptimo de agrupaciones.

| Ventana | Modelo | Captura por grupos (%) | Diagnóstico por predicción (%) | Diferencia (pp) |
|---|---|---:|---:|---:|
| RH | B | 44.6 | 46.9 | +2.4 |
| RH | B_RH | 45.1 | 51.5 | +6.5 |
| QVoice | B | 41.6 | 44.2 | +2.5 |
| QVoice | B_RH | 42 | 49.5 | +7.5 |
| QVoice | B_Q | 41.6 | 47.8 | +6.2 |
| QVoice | B_RH_Q | 42.8 | 50.6 | +7.7 |

El diagnóstico usa la misma capacidad del 30% en cada foto y reparte los empates proporcionalmente. Sólo se conservan resultados agregados; no se publica una lista de personas. Una diferencia positiva indica mayor captura observada al ordenar las predicciones sin la restricción de los grupos actuales; no demuestra un óptimo ni una política operativa.

## Preparaciones y límites del playbook

- El nombre «43 variables» identifica el playbook; contiene 42 vistas analíticas además de portada y navegación. No equivale a 43 columnas independientes.
- Se prepararon 41 incorporaciones RH y 51 QVoice, conservando ocho predictores y dos interacciones de B. Las 33 preguntas comunes están incluidas una sola vez cada una.
- IOS, aplicaciones, Heartbeat exacto y Talent index quedan fuera por las brechas verificadas; Annual Review queda parcialmente representado por promoción y track, con su flag de ciclo pendiente.
- El tiempo en perfil comienza en noviembre de 2025 y el rol almacenado en agosto de 2025. La elegibilidad se determina dentro de cada entrenamiento; preparación no significa historia suficiente.
- La distancia es una aproximación postal a oficinas de la ciudad para Onsite: todo el mapping resolvió por ciudad, hay oficinas alternativas y no hay país de domicilio estructurado. En 2026, 38,044 persona-fotos calculables superan 500 km. No se presenta como commute real validado.
- El catálogo geográfico público de 2026 se usa como aproximación estática retrospectiva. DAL.B está excluido y TIJNA.Z corregido con una entrada válida del catálogo.
- Los catorce indicadores de comentarios usan taxonomías completas congeladas. El prompt de mejora de procesos sólo existe desde 2025; los controles distinguen contenido y disponibilidad.
- Los grupos conservan las dimensiones de B para aislar el aporte de variables. La cantidad se recalcula por foto; el diagnóstico agregado por predicción ayuda a valorar la restricción de esos grupos.
- La búsqueda evalúa todas las incorporaciones individuales y pares/tríos de los seis mejores candidatos internos. No demuestra un óptimo global ni cambia modelos publicados.

La falta de historia verificable se distingue de una variable que sí se probó y no mejoró el modelo. Véase el [inventario por vista del V11](inventario.csv).

### RH

![Incorporaciones individuales](variables-rh.png)

| Incorporación | Periodos | Mejora de Brier (%) | Cambio de captura (pp) | Periodos con mejor Brier |
|---|---:|---:|---:|---:|
| Ciudad laboral | 5/5 | +0.3 | +0.3 | 5 |
| Familia de puesto detallada | 5/5 | +0.3 | +0.2 | 5 |
| Sitio laboral | 5/5 | +0.1 | −<0.1 | 5 |
| Mercado laboral registrado | 5/5 | +0.1 | −<0.1 | 5 |
| País laboral | 5/5 | +0.1 | −<0.1 | 5 |
| Salidas observadas/esperadas del manager, 6 intervalos | 5/5 | +0.1 | +0.3 | 4 |
| Salidas bajo el manager actual, 6 intervalos | 5/5 | +<0.1 | +0.2 | 4 |
| Tiempo en nivel | 5/5 | +<0.1 | +0.6 | 4 |
| Experiencia previa | 5/5 | +<0.1 | −<0.1 | 5 |
| Grado de compensación detallado | 5/5 | +<0.1 | +<0.1 | 4 |
| Región | 5/5 | +<0.1 | −<0.1 | 4 |
| Adquisición registrada | 5/5 | +<0.1 | −<0.1 | 4 |
| Ubicación respecto al manager | 5/5 | +<0.1 | +<0.1 | 3 |
| Salidas del equipo en 6 meses | 5/5 | +<0.1 | +<0.1 | 4 |
| Recencia de salidas del equipo | 5/5 | +<0.1 | 0 | 4 |
| Banda de compa-ratio registrado | 5/5 | +<0.1 | 0 | 3 |
| Salida previa del manager | 5/5 | +<0.1 | +<0.1 | 3 |
| Capa organizacional registrada | 5/5 | +<0.1 | +0.2 | 3 |
| Salidas del equipo en 3 meses | 5/5 | +<0.1 | 0 | 3 |
| Intensidad de salidas del equipo | 5/5 | +<0.1 | 0 | 2 |
| Cambios de manager en 6 meses | 5/5 | +<0.1 | 0 | 3 |
| Prefijo de grado | 5/5 | +<0.1 | 0 | 4 |
| Track de compensación | 5/5 | +<0.1 | 0 | 4 |
| Posición salarial relativa en grupo comparable | 5/5 | +<0.1 | −<0.1 | 3 |
| Coincidencia de sitio y ciudad con el manager | 5/5 | −<0.1 | −<0.1 | 3 |
| Dispersión salarial en equipos comparables | 5/5 | −<0.1 | 0 | 2 |
| Relación horaria con el manager | 5/5 | −<0.1 | −<0.1 | 2 |
| Tamaño del equipo del manager | 5/5 | −<0.1 | 0 | 2 |
| Cambios de manager en 3 meses | 5/5 | −<0.1 | +<0.1 | 1 |
| Profundidad jerárquica reconstruida | 5/5 | −<0.1 | 0 | 1 |
| Adquisición registrada: detalle | 5/5 | −<0.1 | −<0.1 | 0 |
| Tiempo desde entrada observada al grado | 5/5 | -0.1 | -0.2 | 0 |
| Entrada observada al grado actual | 5/5 | -0.1 | -0.2 | 1 |
| Transferencia en 12 meses | 4/5 | +<0.1 | 0 | 4 |
| Salidas sobre benchmark del manager, 18 intervalos | 3/5 | −<0.1 | +0.1 | 1 |
| Aproximación postal a oficinas de la ciudad (Onsite) | 2/5 | +0.1 | −<0.1 | 2 |
| Modalidad en tres grupos del V11 | 2/5 | +<0.1 | 0 | 2 |
| Modalidad de trabajo | 2/5 | +<0.1 | 0 | 2 |
| Grupo de familia de puesto | 0/5 | — | — | 0 |
| Tiempo en perfil de puesto | 0/5 | — | — | 0 |
| Tiempo en rol almacenado: bandas V11 | 0/5 | — | — | 0 |

### QVoice sobre B

![Incorporaciones individuales](variables-qvoice.png)

| Incorporación | Periodos | Mejora de Brier (%) | Cambio de captura (pp) | Periodos con mejor Brier |
|---|---:|---:|---:|---:|
| QVoice: permanecer en Qualcomm (Q4) | 2/2 | +0.3 | 0 | 2 |
| QVoice: promedio de 33 preguntas | 2/2 | +0.2 | 0 | 2 |
| QVoice: poca intención de buscar otro empleo (Q12) | 2/2 | +0.2 | 0 | 2 |
| QVoice: promedio relativo a la región | 2/2 | +0.1 | 0 | 2 |
| QVoice: recomendar Qualcomm (Q1) | 2/2 | +0.1 | 0 | 2 |
| QVoice: pertenencia (Q5) | 2/2 | +0.1 | 0 | 2 |
| QVoice: alcanzar metas de carrera | 2/2 | +0.1 | 0 | 2 |
| QVoice: motivación para dar más (Q3) | 2/2 | +0.1 | 0 | 2 |
| QVoice: procesos que permiten productividad | 2/2 | +0.1 | 0 | 2 |
| QVoice: colaboración entre equipos | 2/2 | +0.1 | 0 | 2 |
| QVoice: cambios para competir (Q17) | 2/2 | +0.1 | 0 | 2 |
| QVoice: comunicación de cambios | 2/2 | +0.1 | 0 | 2 |
| QVoice: aprovechamiento de habilidades | 2/2 | +0.1 | 0 | 2 |
| QVoice: comunicación abierta y honesta | 2/2 | +0.1 | 0 | 2 |
| QVoice: mejora de procesos del equipo | 2/2 | +0.1 | 0 | 2 |
| QVoice: poder ser uno mismo (Q7) | 2/2 | +0.1 | 0 | 2 |
| QVoice: logro personal en el trabajo (Q2) | 2/2 | +0.1 | 0 | 2 |
| QVoice: entender cómo avanzar profesionalmente | 2/2 | +0.1 | 0 | 2 |
| QVoice: energía en el trabajo (Q8) | 2/2 | +0.1 | 0 | 2 |
| QVoice: confianza en decisiones de dirección | 2/2 | +<0.1 | 0 | 2 |
| QVoice: entender las recompensas | 2/2 | +<0.1 | 0 | 2 |
| QVoice: confianza en el futuro (Q13) | 2/2 | +<0.1 | 0 | 2 |
| QVoice: vínculo con objetivos del área | 2/2 | +<0.1 | 0 | 2 |
| QVoice: estímulo para innovar | 2/2 | +<0.1 | 0 | 2 |
| QVoice: comentario sobre confianza y estabilidad laboral | 2/2 | +<0.1 | 0 | 2 |
| QVoice: comentario sobre carrera y promoción | 2/2 | +<0.1 | 0 | 2 |
| QVoice: presencia de comentario de mejora | 2/2 | +<0.1 | 0 | 2 |
| QVoice: expresar ideas diferentes | 2/2 | +<0.1 | 0 | 2 |
| QVoice: plantear inquietudes éticas | 2/2 | +<0.1 | 0 | 2 |
| QVoice: estrés manejable (Q11) | 2/2 | +<0.1 | 0 | 2 |
| QVoice: feedback del manager | 2/2 | +<0.1 | 0 | 2 |
| QVoice: trato respetuoso | 2/2 | +<0.1 | 0 | 2 |
| QVoice: reconocimiento | 2/2 | +<0.1 | 0 | 2 |
| QVoice: comentario sobre modalidad y traslado | 2/2 | +<0.1 | 0 | 1 |
| QVoice: mención de trabajo híbrido | 2/2 | +<0.1 | 0 | 1 |
| QVoice: inquietud de política presencial | 2/2 | +<0.1 | 0 | 2 |
| QVoice: presencia de algún comentario | 2/2 | +<0.1 | 0 | 1 |
| QVoice: mención de asistencia a oficina | 2/2 | +<0.1 | 0 | 1 |
| QVoice: energía después del trabajo (Q10) | 2/2 | +<0.1 | 0 | 2 |
| QVoice: comentario sobre manager, liderazgo y respeto | 2/2 | +<0.1 | 0 | 1 |
| QVoice: comentario sobre carga de trabajo y equilibrio personal | 2/2 | +<0.1 | 0 | 1 |
| QVoice: petición de flexibilidad remota o híbrida | 2/2 | +<0.1 | 0 | 1 |
| QVoice: mención de trabajo remoto | 2/2 | +<0.1 | 0 | 1 |
| QVoice: cooperación entre compañeros | 2/2 | +<0.1 | 0 | 2 |
| QVoice: comentario sobre recompensas | 2/2 | +<0.1 | 0 | 1 |
| QVoice: apoyo del manager al equilibrio personal | 2/2 | +<0.1 | 0 | 2 |
| QVoice: manager que elimina obstáculos | 2/2 | +<0.1 | 0 | 1 |
| QVoice: comentario sobre herramientas, procesos y burocracia | 2/2 | +<0.1 | 0 | 1 |
| QVoice: cuestionar formas tradicionales | 2/2 | +<0.1 | 0 | 2 |
| QVoice: equilibrio trabajo y vida | 2/2 | +<0.1 | 0 | 1 |
| QVoice: disponibilidad de respuestas | 2/2 | −<0.1 | 0 | 1 |

## Estabilidad y límites

| Comparación pareada | IC 95% del cambio de captura (pp) |
|---|---:|
| B_RH frente a B | -0.1 a +1 |
| B_Q frente a B | 0 a 0 |
| B_RH_Q frente a B | +0.2 a +2.1 |
| B_Q frente a B_refresh | 0 a 0 |
| B_RH_Q frente a B_RH_refresh | +0.3 a +1.4 |

Intervalos con personas completas remuestreadas en RAM, conservando juntas sus observaciones y dando el mismo peso a cada periodo. Son condicionales a las selecciones ya realizadas; no convierten una búsqueda retrospectiva en confirmación prospectiva.

- Evaluación retrospectiva en años explorados previamente; requiere confirmación prospectiva.
- Shortlist interna de seis para pares y tríos; no es el óptimo global de todas las combinaciones.
- QVoice tiene dos periodos externos; el primer corte requiere validación mensual interna.
- Tiempo en perfil de puesto aparece desde noviembre de 2025 y no tiene historia interna suficiente.
- No se reconstruye fecha real de publicación QVoice: se aplica la política anual aprobada.
- Career cambia de redacción en 2024; su transporte es exploratorio.
- Los predictores RH y QVoice se mantienen constantes al calcular los seis meses, salvo calendario.
- IOS, aplicaciones, Heartbeat exacto y Talent index quedan fuera por las brechas verificadas; Annual Review queda parcialmente representado por promoción y track, con su flag de ciclo pendiente.
- El tiempo en perfil comienza en noviembre de 2025 y el rol almacenado en agosto de 2025. La elegibilidad se determina dentro de cada entrenamiento; preparación no significa historia suficiente.
- La distancia es una aproximación postal a oficinas de la ciudad para Onsite: todo el mapping resolvió por ciudad, hay oficinas alternativas y no hay país de domicilio estructurado. En 2026, 38,044 persona-fotos calculables superan 500 km. No se presenta como commute real validado.
- El catálogo geográfico público de 2026 se usa como aproximación estática retrospectiva. DAL.B está excluido y TIJNA.Z corregido con una entrada válida del catálogo.
- Los catorce indicadores de comentarios usan taxonomías completas congeladas. El prompt de mejora de procesos sólo existe desde 2025; los controles distinguen contenido y disponibilidad.

La posición salarial relativa sólo se calcula en grupos de cinco o más personas con el mismo manager, país, grado y moneda; el resto mantiene una categoría no comparable. La dispersión usa grupos comparables de dos o más. Sus importes se quedan dentro de SQL.

## Evidencia y reproducción

- [Inventario completo y motivo de cada exclusión](inventario.csv).
- [Resultados por variable](comparacion-variables.csv) y [resultados completos](results.json).
- [Consultas y evidencia de entradas](evidence-ledger.json).
- [Configuración congelada](frozen-config.json), [validación](verification.json) y [manifest](manifest.json).
- `selection/`: decisiones internas; `periods/`: evaluación externa; `models/`: artefactos experimentales reproducibles.

Las categorías infrecuentes de las incorporaciones RH se agrupan sólo a partir de entrenamiento. Los ocho predictores de B y sus dos interacciones siempre permanecen. No se modificaron scores de assessment ni se guardaron filas, llaves o predicciones individuales.
