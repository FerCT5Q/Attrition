# Qué se hizo con cada variable del playbook V11

Diccionario de modelado y decisiones de la ejecución `engineering-b-playbook-v11-20261012-v1`. Modo `presentation`; sólo agregados y metadatos, sin filas ni predicciones individuales.

Se documentan **102 representaciones**: los **10 términos obligatorios de B**, **41 incorporaciones de RH** y **51 de QVoice**. El archivo llamado «43 variables» contiene **42 vistas analíticas**, además de portada/navegación; varias vistas comparten variables y otras contienen múltiples preguntas.

Cada ficha contiene valores de origen, bandas/categorías, transformación exacta, tratamiento de faltantes, fecha de conocimiento, pruebas, decisiones por periodo y motivo. Las referencias y niveles concretos se extraen de los modelos guardados.

Las fichas describen la implementación ejecutada. Cuando el alcance previo requiere una precisión, se añade una nota del tratamiento efectivo en la correspondencia del playbook.

[Abrir diccionario en Excel](diccionario.xlsx) · [Tabla CSV](diccionario.csv) · [Decisiones CSV](decisiones.csv) · [Codificaciones CSV](codificaciones.csv) · [Informe de resultados](informe.md)

## Selección final experimental

**RH añadido a B:** Familia de puesto detallada, Ciudad laboral, Aproximación postal a oficinas de la ciudad (Onsite).

- **QVoice sobre B:** QVoice: permanecer en Qualcomm (Q4), QVoice: poca intención de buscar otro empleo (Q12). Tipo de ajuste guardado: `q`.
- **QVoice sobre B_RH:** QVoice: permanecer en Qualcomm (Q4), QVoice: poca intención de buscar otro empleo (Q12). Tipo de ajuste guardado: `q`.

Corte final: 2026-09-07. La evaluación temporal corresponde a selecciones hechas en cortes anteriores; no se evalúan retrospectivamente estos coeficientes finales como si fueran externos.

## Cómo leer las decisiones

«Obligatoria en B» significa que se conservó por instrucción. «No seleccionada» tiene un motivo por corte: historia insuficiente, ajuste fallido, condiciones incumplidas o una alternativa con mejor resultado bajo la regla de parsimonia. Una variable puede ser seleccionada en combinación aunque no cumpla las condiciones por sí sola. Las exclusiones anteriores a la selección aparecen separadas, con su causa y lo que falta resolver.

Todas las entradas son categorías con indicadores 0/1. La referencia es la categoría más frecuente por filas de entrenamiento y se omite. Cada categoría restante tiene su propio indicador. Una categoría no aprendida deja todos los indicadores de ese término en cero. Las bandas no se usan como números ordinales ni se estandarizan como variables continuas.

Por ejemplo, una binaria de origen con valores sí/no y un estado desconocido puede producir tres categorías y dos indicadores. El número concreto depende de los niveles presentes y de la referencia que aparece en el archivo de codificaciones.

Sólo incorporaciones RH: conserva categorías con al menos 300 personas distintas en todo el entrenamiento; el resto, incluidas categorías nuevas o desconocidos infrecuentes, se transforma en (other). B y QVoice no usan este pooling. Una persona puede contar en más de una categoría si cambió durante el entrenamiento; no es un mínimo por foto.

B conserva ocho predictores y dos interacciones. Se prueban todas las incorporaciones individuales; pares y tríos sólo entre las seis primeras de la reserva interna. RH ordena las individuales ajustadas y elegibles; QVoice ordena las ajustadas, y filtra disponibilidad y condiciones de validación al elegir el resultado. No se crean interacciones nuevas entre candidatas. Las tres penalizaciones de B y QVoice son 0.1, 1 y 10; RH usa la elegida para B en cada corte. Para cada conjunto QVoice se elige primero la penalización con menor log-loss interno; la comparación de disponibilidad y las condiciones se aplican a ese ajuste representativo del conjunto.

Ajuste válido y elegibilidad; Brier no empeora; PR-AUC ≥99% del control. En validación de seis meses, además: lift al 10% ≥99% del control, MAE de los mismos grupos ≤control+0.1 pp y captura ≥control−0.5 pp. Entre las opciones que cumplen se minimiza log-loss y se aplica parsimonia dentro de una tolerancia relativa exacta de 0.0005. Se escoge la opción con menos incorporaciones dentro de esa ventana; después log-loss e identificador.

QVoice añade un ajuste a la predicción de B o B+RH, conservando los términos de esa base. Se compara con la base fija, un ajuste sólo de intercepto y un control de disponibilidad emparejado. El contenido debe superar en log-loss a su control de disponibilidad. Los estados de ausencia no se rellenan como respuestas desfavorables.

Sobre B+RH, la búsqueda QVoice está condicionada a las incorporaciones RH elegidas para ese corte externo. Los coeficientes de la base se vuelven a ajustar antes de la reserva QVoice; no es una búsqueda conjunta de todas las combinaciones RH×QVoice.

Las decisiones internas reservan tres fotos previas con seguimiento conocido. El primer corte QVoice usa una reserva mensual por historia corta; después se usa seguimiento de seis meses. Las variables RH requieren seis fotos observables de entrenamiento y más de una categoría después de agrupar las poco frecuentes.

Los grupos conservan antigüedad × salidas del equipo × nivel para comparar el aporte de variables. Se recalcula su cantidad por foto; esta ronda no optimiza nuevas dimensiones de agrupación. El informe adjunto contiene el diagnóstico agregado de captura sin la restricción de estos grupos.

La captura principal usa capacidad del 30% de la población en cada foto. Se ordenan grupos elegibles de al menos 300 personas por su riesgo medio; el último grupo puede contribuir parcialmente y los empates se reparten proporcionalmente. Es un cálculo agregado, sin lista de personas priorizadas.

## Fichas de las variables

### Base B obligatoria

| Ficha | Identificador | Tipo de entrada | Selección para periodos externos | Selección final |
|---|---|---|---|---|
| [Nivel agrupado](fichas/level_grouped.md) | level_grouped | Categoría nominal | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Antigüedad desde ingreso original](fichas/tenure_playbook_band.md) | tenure_playbook_band | Numérica transformada en bandas nominales | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Mes calendario](fichas/calendar_month.md) | calendar_month | Calendario categórico | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Cambios de manager en 12 meses](fichas/manager_changes_12m.md) | manager_changes_12m | Conteo transformado en categoría | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Salidas del equipo en 12 meses](fichas/team_exits_12m.md) | team_exits_12m | Conteo transformado en categoría | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Reportes directos](fichas/direct_reports_band.md) | direct_reports_band | Conteo transformado en categoría | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Tiempo desde última promoción](fichas/time_since_promotion_band.md) | time_since_promotion_band | Historia de eventos transformada en categoría | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Recontratación](fichas/rehire.md) | rehire | Binaria observada con categoría desconocida | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Interacción: nivel y antigüedad](fichas/level_x_tenure.md) | level_x_tenure | Interacción categórica explícita | B: seleccionada en 5 de 5 cortes | Obligatoria |
| [Interacción: antigüedad y cambios de manager](fichas/tenure_x_manager_changes.md) | tenure_x_manager_changes | Interacción categórica explícita | B: seleccionada en 5 de 5 cortes | Obligatoria |

### Incorporaciones RH

| Ficha | Identificador | Tipo de entrada | Selección para periodos externos | Selección final |
|---|---|---|---|---|
| [Experiencia previa](fichas/prior_experience_band.md) | prior_experience_band | Numérica transformada en bandas nominales | B: seleccionada en 1 de 5 cortes | No seleccionada al corte final |
| [Tiempo en nivel](fichas/time_at_level_band.md) | time_at_level_band | Duración derivada, por bandas | B: seleccionada en 1 de 5 cortes | No seleccionada al corte final |
| [Salida previa del manager](fichas/manager_left_6m.md) | manager_left_6m | Binaria registrada | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Capa organizacional registrada](fichas/layers_band.md) | layers_band | Numérica almacenada, por categorías | B: seleccionada en 1 de 5 cortes | No seleccionada al corte final |
| [Modalidad de trabajo](fichas/work_arrangement_group.md) | work_arrangement_group | Categoría agrupada | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Región](fichas/region.md) | region | Categoría nominal | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Banda de compa-ratio registrado](fichas/comp_ratio_band.md) | comp_ratio_band | Razón almacenada transformada en bandas | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Prefijo de grado](fichas/grade_family.md) | grade_family | Categoría agrupada | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Adquisición registrada](fichas/acquisition_recorded.md) | acquisition_recorded | Binaria de presencia de registro | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Transferencia en 12 meses](fichas/transfer_12m.md) | transfer_12m | Binaria de evento con historia desconocida | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Cambios de manager en 3 meses](fichas/manager_changes_3m.md) | manager_changes_3m | Conteo transformado en categoría | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Cambios de manager en 6 meses](fichas/manager_changes_6m.md) | manager_changes_6m | Conteo transformado en categoría | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Salidas del equipo en 3 meses](fichas/team_exits_3m.md) | team_exits_3m | Conteo transformado en categoría | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Salidas del equipo en 6 meses](fichas/team_exits_6m.md) | team_exits_6m | Conteo transformado en categoría | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Recencia de salidas del equipo](fichas/team_exit_recency_12m.md) | team_exit_recency_12m | Recencia categórica | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Tamaño del equipo del manager](fichas/manager_team_size_band.md) | manager_team_size_band | Conteo por bandas | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Intensidad de salidas del equipo](fichas/team_exit_intensity_12m.md) | team_exit_intensity_12m | Tasa derivada por bandas | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Familia de puesto detallada](fichas/job_family_detail.md) | job_family_detail | Categoría nominal | B: seleccionada en 5 de 5 cortes | sobre B |
| [Grupo de familia de puesto](fichas/job_family_group.md) | job_family_group | Categoría nominal | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [País laboral](fichas/work_country.md) | work_country | Categoría nominal | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Sitio laboral](fichas/work_site.md) | work_site | Categoría nominal compuesta | B: seleccionada en 1 de 5 cortes | No seleccionada al corte final |
| [Grado de compensación detallado](fichas/compensation_grade_detail.md) | compensation_grade_detail | Categoría nominal | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Tiempo en perfil de puesto](fichas/time_in_job_profile_band.md) | time_in_job_profile_band | Duración derivada por bandas | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Ubicación respecto al manager](fichas/manager_location_relation.md) | manager_location_relation | Categoría nominal derivada | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Posición salarial relativa en grupo comparable](fichas/within_team_pay_position.md) | within_team_pay_position | Percentil interno transformado en categoría | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Dispersión salarial en equipos comparables](fichas/manager_pay_spread_band.md) | manager_pay_spread_band | Categoría derivada de dispersión | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Ciudad laboral](fichas/work_city.md) | work_city | Categoría nominal compuesta | B: seleccionada en 4 de 5 cortes | sobre B |
| [Mercado laboral registrado](fichas/labor_market_detail.md) | labor_market_detail | Categoría nominal | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Modalidad en tres grupos del V11](fichas/work_arrangement_v11.md) | work_arrangement_v11 | Categoría nominal agrupada | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Adquisición registrada: detalle](fichas/acquisition_detail.md) | acquisition_detail | Categoría nominal | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Entrada observada al grado actual](fichas/current_grade_entry_path.md) | current_grade_entry_path | Categoría derivada de historia | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Tiempo desde entrada observada al grado](fichas/time_since_grade_entry_band.md) | time_since_grade_entry_band | Duración derivada por bandas | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Track de compensación](fichas/pay_track_detail.md) | pay_track_detail | Categoría nominal extraída | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Profundidad jerárquica reconstruida](fichas/hierarchy_depth_band.md) | hierarchy_depth_band | Profundidad reconstruida, por categorías | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Salidas observadas/esperadas del manager, 6 intervalos](fichas/manager_observed_expected6_band.md) | manager_observed_expected6_band | Razón derivada por bandas | B: seleccionada en 2 de 5 cortes | No seleccionada al corte final |
| [Salidas bajo el manager actual, 6 intervalos](fichas/manager_team_exits6_v11.md) | manager_team_exits6_v11 | Conteo de eventos por categoría | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Salidas sobre benchmark del manager, 18 intervalos](fichas/manager_above_average18.md) | manager_above_average18 | Binaria derivada con historia desconocida | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Coincidencia de sitio y ciudad con el manager](fichas/manager_colocation_v11.md) | manager_colocation_v11 | Binaria derivada con categoría desconocida | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Relación horaria con el manager](fichas/manager_timezone_relation.md) | manager_timezone_relation | Categoría nominal derivada | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |
| [Aproximación postal a oficinas de la ciudad (Onsite)](fichas/commute_distance_onsite_v11.md) | commute_distance_onsite_v11 | Distancia aproximada por bandas nominales | B: seleccionada en 0 de 5 cortes | sobre B |
| [Tiempo en rol almacenado: bandas V11](fichas/time_in_role_stored_v11.md) | time_in_role_stored_v11 | Numérica almacenada transformada en bandas | B: seleccionada en 0 de 5 cortes | No seleccionada al corte final |

### Incorporaciones QVoice

| Ficha | Identificador | Tipo de entrada | Selección para periodos externos | Selección final |
|---|---|---|---|---|
| [QVoice: cuestionar formas tradicionales](fichas/qv_M01.md) | qv_M01 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: equilibrio trabajo y vida](fichas/qv_M02.md) | qv_M02 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: expresar ideas diferentes](fichas/qv_M03.md) | qv_M03 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: trato respetuoso](fichas/qv_M04.md) | qv_M04 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: plantear inquietudes éticas](fichas/qv_M05.md) | qv_M05 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: vínculo con objetivos del área](fichas/qv_M06.md) | qv_M06 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: poder ser uno mismo (Q7)](fichas/qv_M07.md) | qv_M07 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: estímulo para innovar](fichas/qv_M08.md) | qv_M08 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: energía en el trabajo (Q8)](fichas/qv_M09.md) | qv_M09 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: pertenencia (Q5)](fichas/qv_M10.md) | qv_M10 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: confianza en decisiones de dirección](fichas/qv_M11.md) | qv_M11 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: confianza en el futuro (Q13)](fichas/qv_M12.md) | qv_M12 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: energía después del trabajo (Q10)](fichas/qv_M13.md) | qv_M13 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: poca intención de buscar otro empleo (Q12)](fichas/qv_M14.md) | qv_M14 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 1 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | sobre B, sobre B_RH |
| [QVoice: reconocimiento](fichas/qv_M15.md) | qv_M15 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: permanecer en Qualcomm (Q4)](fichas/qv_M16.md) | qv_M16 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 2 de 2 cortes; B_RH: seleccionada en 1 de 2 cortes | sobre B, sobre B_RH |
| [QVoice: entender las recompensas](fichas/qv_M17.md) | qv_M17 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: entender cómo avanzar profesionalmente](fichas/qv_M18.md) | qv_M18 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: recomendar Qualcomm (Q1)](fichas/qv_M19.md) | qv_M19 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 1 de 2 cortes; B_RH: seleccionada en 1 de 2 cortes | No seleccionada al corte final |
| [QVoice: aprovechamiento de habilidades](fichas/qv_M20.md) | qv_M20 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: feedback del manager](fichas/qv_M21.md) | qv_M21 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: manager que elimina obstáculos](fichas/qv_M22.md) | qv_M22 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: apoyo del manager al equilibrio personal](fichas/qv_M23.md) | qv_M23 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: mejora de procesos del equipo](fichas/qv_M24.md) | qv_M24 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: logro personal en el trabajo (Q2)](fichas/qv_M25.md) | qv_M25 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comunicación de cambios](fichas/qv_M26.md) | qv_M26 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: cambios para competir (Q17)](fichas/qv_M27.md) | qv_M27 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: motivación para dar más (Q3)](fichas/qv_M28.md) | qv_M28 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: estrés manejable (Q11)](fichas/qv_M29.md) | qv_M29 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: cooperación entre compañeros](fichas/qv_M30.md) | qv_M30 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: procesos que permiten productividad](fichas/qv_M31.md) | qv_M31 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: colaboración entre equipos](fichas/qv_M32.md) | qv_M32 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comunicación abierta y honesta](fichas/qv_M33.md) | qv_M33 | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: alcanzar metas de carrera](fichas/qv_career.md) | qv_career | Binaria favorable registrada con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: promedio de 33 preguntas](fichas/qv_mean33.md) | qv_mean33 | Promedio de binarias transformado en bandas | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: disponibilidad de respuestas](fichas/qv_availability.md) | qv_availability | Indicador categórico de disponibilidad | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: promedio relativo a la región](fichas/qv_region_relative.md) | qv_region_relative | Promedio relativo contemporáneo transformado en bandas | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: presencia de algún comentario](fichas/qv_comment_presence.md) | qv_comment_presence | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: presencia de comentario de mejora](fichas/qv_improvement_comment_presence.md) | qv_improvement_comment_presence | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comentario sobre recompensas](fichas/qv_comment_rewards.md) | qv_comment_rewards | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comentario sobre carrera y promoción](fichas/qv_comment_career.md) | qv_comment_career | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comentario sobre manager, liderazgo y respeto](fichas/qv_comment_leadership.md) | qv_comment_leadership | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comentario sobre carga de trabajo y equilibrio personal](fichas/qv_comment_workload.md) | qv_comment_workload | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comentario sobre modalidad y traslado](fichas/qv_comment_arrangement.md) | qv_comment_arrangement | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comentario sobre herramientas, procesos y burocracia](fichas/qv_comment_processes.md) | qv_comment_processes | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: comentario sobre confianza y estabilidad laboral](fichas/qv_comment_confidence.md) | qv_comment_confidence | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: mención de trabajo remoto](fichas/qv_comment_remote.md) | qv_comment_remote | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: mención de trabajo híbrido](fichas/qv_comment_hybrid.md) | qv_comment_hybrid | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: mención de asistencia a oficina](fichas/qv_comment_office.md) | qv_comment_office | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: petición de flexibilidad remota o híbrida](fichas/qv_remote_hybrid_request.md) | qv_remote_hybrid_request | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |
| [QVoice: inquietud de política presencial](fichas/qv_onsite_policy_concern.md) | qv_onsite_policy_concern | Indicador textual derivado con estados de ausencia | B: seleccionada en 0 de 2 cortes; B_RH: seleccionada en 0 de 2 cortes | No seleccionada al corte final |

## Conceptos excluidos o sin nueva columna

| Ficha | Decisión | Motivo |
|---|---|---|
| [Movimientos IOS](fichas/exclusion-ios.md) | Excluida antes de selección | No se verificó conocimiento histórico de las resoluciones IOS. |
| [Solicitudes de empleo](fichas/exclusion-applications.md) | Excluida antes de selección | Falta continuidad del feed exacto V11 y evidencia temporal suficiente de la alternativa. |
| [Engineering frente a otras funciones](fichas/exclusion-engineering.md) | Constante dentro de la población | No permite distinguir riesgos entre personas de Engineering. |
| [Género](fichas/exclusion-gender.md) | Fuera de autorización de predicción | La autorización vigente excluye su uso como predictor; no es un resultado de desempeño. |
| [Heartbeat exacto de QVoice](fichas/exclusion-heartbeat.md) | Excluida antes de selección | No se dispone de la estructura exacta requerida para las waves elegibles. |
| [Flag de promoción de Annual Review](fichas/exclusion-annual_review.md) | Representación exacta excluida; concepto parcialmente cubierto | El grain y el dominio pasan el control técnico, pero esos timestamps no habilitan usar el flag en años anteriores. |
| [Talent index](fichas/exclusion-talent.md) | Excluida antes de selección | No hay ancla de negocio suficiente para reproducir lo conocido en cada foto. |

## Archivos y trazabilidad

- `diccionario.xlsx`: guía, transformaciones, decisiones, valores aprendidos, correspondencia V11, exclusiones y soporte anual.
- `diccionario.csv` y `fichas/`: consulta por variable.
- `decisiones.json` y `decisiones.csv`: decisiones por variable, periodo y base; el JSON conserva métricas y límites exactos.
- `codificaciones.json` y `codificaciones.csv`: referencias y categorías realmente aprendidas por cada modelo, incluidos los externos.
- `vistas-playbook.csv`: correspondencia de las 42 vistas del V11.
- `manifest.json`: hashes propios y del manifest de entrenamiento. Este suplemento no altera los artefactos congelados.

Las fichas documentan el código ejecutado; no elevan scores ni afirman lineage oficial donde sigue pendiente. Las fórmulas y JSON/CSV conservan la precisión de la evidencia; las tablas de resultados visibles usan como máximo un decimal.
