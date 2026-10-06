# QVoice heartbeat por item

## Resumen

QVoice heartbeat es una senal descriptiva y restringida para revisar que
items de QVoice quedan relativamente por encima o por debajo del promedio de
respuestas de cada persona. Se presenta como evidencia agregada; no es una
evaluacion individual, una etiqueta de riesgo ni una feature productiva
aprobada.

La vista usa la wave Jan-2026 y los 53 items con escala 1-5 scale definidos
en survey_structure.xlsx. El denominador de workforce es el snapshot HRDA
del 2025-12-28: worker_type='Employee', employee_type='Regular' y
active_status=1.

## Definicion ejecutable

1. Se deduplica la fuente por Emp ID. Las claves faltantes, invalidas o con
   respuestas conflictivas no entran al calculo.
2. Para cada persona se calcula el promedio de sus respuestas 1-5 validas
   cuando tiene al menos 70% de los items validos: 38 de 53.
3. Para cada item valido se calcula una reaccion relativa:
   - +1: la respuesta esta por encima del promedio personal;
   - 0: la respuesta es igual al promedio personal;
   - -1: la respuesta esta por debajo del promedio personal.
4. Los faltantes o valores invalidos no se convierten en 0; se excluyen del
   denominador del item.

El grafico publica los tres items con mayor proporcion de +1 y los tres con
mayor proporcion de -1. Para cada item seleccionado presenta siempre los tres
signos relativos (+1, 0 y -1), que son mutuamente excluyentes y suman 100.0%
del denominador de respuestas validas de ese item. No presenta favorabilidad
absoluta (4-5): esta vista no usa favorable, no favorable ni neutro de la
escala; el 0 significa solamente que la respuesta fue igual al promedio
personal.

Cada una de las 18 barras tambien muestra la tasa de attrition de su propio
segmento pregunta/signo. El n y las salidas se mantienen en el detalle
emergente de la barra para conservar una lectura visual simple.

## Attrition post-survey YTD

La comparacion de attrition es descriptiva y se calcula por separado para
cada segmento pregunta/signo:

1. Cohorte base: empleados `Regular` activos (`worker_type='Employee'`,
   `employee_type='Regular'`, `active_status=1`) al cierre mensual del
   2025-12-28, antes de la wave Jan-2026.
2. Ventana de resultado: desde despues del lanzamiento de QVoice el
   2026-01-07 hasta el cierre fiscal de agosto, 2026-08-23.
3. Evento: al menos una terminacion con `term_type` exactamente `VOLUNTARY`.
4. Tasa: salidas voluntarias del segmento / empleados del mismo segmento que
   empatan con la cohorte base.

Por tanto es **attrition post-survey YTD** y **no esta anualizado**. No es una
ventana movil de 12 meses. Dentro de una pregunta, cada persona pertenece a
un solo signo; la misma persona puede aparecer en distintas preguntas y las
tasas entre preguntas no se suman.

## Mapping y fuente

El mapping de question_id, kpis y driver proviene unicamente de
data/QVoice/survey_structure.xlsx. La fuente primaria de respuestas es
data/QVoice/Jan 2026 Qvoice_raw data.xlsx, hoja Raw data. La tabla
hrda.qvoice_survey_data solo se usa en la reconciliacion agregada de wave;
sus campos binarios no sustituyen las respuestas 1-5 del workbook.

El join de elegibilidad se ejecuta en lotes agregados contra
hrda.post_hire_monthly_worker_dtls. Las mascaras binarias usadas durante el
join son temporales y no se persisten.

## Interpretacion y limites

- +1 significa "por encima del promedio de esa persona", no necesariamente
  una opinion favorable en terminos absolutos.
- La senal es transversal para Jan-2026; no mide cambio temporal entre waves.
- No demuestra causalidad, satisfaccion, intencion de salida ni que la
  opinion haya causado una salida. La tasa post-survey solo describe lo que
  ocurrio al segmento observado en esa ventana YTD.
- No se publica como alerta individual, score de manager o feature operativa.
- Todas las etiquetas visibles cumplen n >= 30.
- La presentacion mantiene solo conteos, porcentajes y metadatos agregados; no
  contiene IDs, nombres, correos, respuestas individuales ni texto libre.

## Evidencia y reproducibilidad

- Workforce: queries/profiles/qvoice_heartbeat_workforce_denominator_20260911.sql
- Reconciliacion: queries/audits/qvoice_heartbeat_workforce_reconciliation_20260911.sql
- Definicion de ventana y auditoria de cohorte:
  queries/audits/qvoice_heartbeat_relative_sign_ytd_window_audit_20260923.sql
- Join agregado temporal por pregunta/signo:
  queries/audits/qvoice_heartbeat_relative_sign_ytd_attrition_runtime_template_20260923.sql
- Builder del ranking: tools/build_qvoice_heartbeat_evidence.py
- Builder de attrition post-survey YTD:
  tools/build_qvoice_heartbeat_relative_sign_ytd_attrition_evidence.py
- Evidencia de ranking congelada:
  output/distribution/json/qvoice-heartbeat-evidence-20260911.json
- Evidencia de los 18 segmentos:
  output/distribution/json/qvoice-2026-august-post-survey-ytd-heartbeat-relative-sign-attrition-evidence-20260923.json

Resultado de la ejecucion del 2026-09-11:

- workforce elegible: 47,134;
- filas raw: 42,203;
- claves duplicadas o conflictivas: 0;
- empleados raw emparejados con workforce: 39,194;
- personas con promedio personal elegible: 37,605;
- items publicables: 53.

La evidencia post-survey YTD se ejecuta el 2026-09-23 y valida dos rankings,
seis preguntas y 18 segmentos publicables (`n >= 30`); cada terna de signos
reconcilia tanto a 100.0% como a la tasa basada en salidas y cohorte
emparejada.
