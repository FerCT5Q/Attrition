# Inventario de variables para C

| Orden | Concepto | Estado | Representación o razón |
|---:|---|---|---|
| 1 | Applied to a job | excluida o pendiente | Fuente de applications sin enlace completo y autorización operativa; queda pendiente. |
| 2 | More than 3 job applications | excluida o pendiente | Misma limitación de applications. |
| 3 | Transfer within past year | candidata o representación parcial | transfer_12m; ios_12m |
| 4 | Location | excluida o pendiente | Geografía representada por región; granularidad de sitio queda fuera de esta búsqueda. |
| 5 | Within team compensation range | excluida o pendiente | Requiere denominador y grupo comparable de compensación; pendiente. |
| 6 | Team turnover | candidata o representación parcial | team_exits_12m; direct_reports_band (conteos, no tasa) |
| 7 | More than 1 employee leaves in a year | candidata o representación parcial | team_exits_12m |
| 8 | Job family | excluida o pendiente | Granularidad adicional no prioritaria de este experimento; pendiente. |
| 9 | Region | candidata o representación parcial | region |
| 10 | Gender | excluida o pendiente | Atributo protegido excluido del predictor. |
| 11 | Remote / hybrid / in office status | candidata o representación parcial | work_arrangement_group |
| 12 | Engineering vs. non-engineering | excluida o pendiente | Constante por definición de población Engineering. |
| 13 | Rehire | candidata o representación parcial | rehire (proxy service_date) |
| 14 | Years of experience prior to Qualcomm | candidata o representación parcial | prior_experience_band |
| 15 | Commute distance | excluida o pendiente | No hay integración histórica aprobada de domicilio/distancia para esta búsqueda. |
| 16 | RTO/hybrid comment in Qvoice | excluida o pendiente | QVoice excluido por instrucción; reservado para C + Q. |
| 17 | Any comment on Qvoice | excluida o pendiente | QVoice excluido por instrucción; reservado para C + Q. |
| 18 | Non-respondents | excluida o pendiente | QVoice excluido por instrucción; reservado para C + Q. |
| 19 | Intent to Stay items | excluida o pendiente | QVoice excluido por instrucción; reservado para C + Q. |
| 20 | Career goals item | excluida o pendiente | QVoice excluido por instrucción; reservado para C + Q. |
| 21 | Average of all Qvoice items | excluida o pendiente | QVoice excluido por instrucción; reservado para C + Q. |
| 22 | Standardized / normalized within region | excluida o pendiente | QVoice excluido por instrucción; reservado para C + Q. |
| 23 | Tech industry unemployment data | excluida o pendiente | Fuente externa no integrada temporalmente. |
| 24 | Draup data | excluida o pendiente | Fuente externa no integrada temporalmente. |
| 25 | LinkedIn scraping | excluida o pendiente | Fuente externa no integrada temporalmente. |
| 26 | Position / time in level | candidata o representación parcial | time_at_level_band |
| 27 | Company tenure | candidata o representación parcial | tenure_playbook_band |
| 28 | Time since last promotion | candidata o representación parcial | time_since_promotion_band |
| 29 | Promoted vs. hired into level | candidata o representación parcial | time_since_promotion_band + rehire (parcial; no equivalencia completa) |
| 30 | Level | candidata o representación parcial | level_grouped |
| 31 | Layers from CEO | candidata o representación parcial | layers_band (valor almacenado; no profundidad reconstruida al CEO) |
| 32 | Compensation grade | candidata o representación parcial | grade_family (prefijo, no todos los grados) |
| 33 | Comp ratio | candidata o representación parcial | comp_ratio_band (valor almacenado) |
| 34 | Co-location with manager | excluida o pendiente | Join histórico con ubicación de manager pendiente. |
| 35 | Hours away from manager | excluida o pendiente | Derivación de distancia/tiempo con manager pendiente. |
| 36 | High risk manager | excluida o pendiente | Definición de alto riesgo puede ser circular; no se usa. |
| 37 | High turnover under this person | excluida o pendiente | La señal utilizada es salida del equipo actual, no reputación histórica de una persona. |
| 38 | Manager leaving | candidata o representación parcial | manager_left_6m |
| 39 | Manager change | candidata o representación parcial | manager_changes_12m |
| 40 | Number of manager changes | candidata o representación parcial | manager_changes_12m |
| 41 | Talent index | excluida o pendiente | Definición e historia de talent index pendientes. |
| 42 | Major inflection points | candidata o representación parcial | transfer_12m, manager_changes_12m y promoción (parcial) |
| 43 | ET fields | excluida o pendiente | Se evitan etiquetas de líderes e identificadores; jerarquía detallada pendiente. |
| 44 | Adquisición registrada (adición del playbook) | candidata | acquisition_recorded |
| 45 | Tamaño de equipo directo (adición del playbook) | candidata | direct_reports_band |
