# Revisión conjunta: modelos, grupos y preparación para RH

Ejecución `engineering-julia-rh-review-20261012-v1`, cerrada el 13-oct-2026.
Modo `presentation`. Engineering, Employee, Regular, activa y sin RF360;
fotos de agosto–diciembre de 2025 y enero–febrero de 2026, salida voluntaria
a seis meses e igual peso por periodo. `job_family_detail` queda excluida.

La revisión consolida aportaciones de varias personas, sin atribución
individual. La presentación parte del modelo inicial y sus limitaciones o
preguntas; después muestra pruebas, mejoras medidas y pendientes. Una
comprobación pendiente, como equidad, no se presenta como un fallo demostrado.

CQ sigue elegido. FQ + BU L3 obtiene el menor log-loss y Brier medios en esta
comparación retrospectiva. FQ añade ciudad laboral a C + QVoice; FQ + BU L3
añade además el mapping histórico de unidad. Se restauró CQ y se conservaron
las variables y penalizaciones seleccionadas antes de cada periodo.

Los orígenes de ajuste RH difieren en enero: CQ conserva la base histórica de
1-ago-2025, mientras FQ/FQ + BU se reajustan a 1-ene-2026. Por ello se comparan
estimadores completos y la diferencia frente a CQ en enero reúne ciudad y
actualización de la base. No aísla el aporte de ciudad. FQ frente a FQ + BU
comparte origen RH en ambos periodos.

| Modelo | Log-loss ×1000 | Brier ×1000 | Captura al 30% | Error grupo-mes |
|---|---:|---:|---:|---:|
| CQ | 137.7 | 30.7 | 43.1% | 1 pp |
| FQ | 136.4 | 30.6 | 43.1% | 0.9 pp |
| FQ + BU L3 | 136 | 30.6 | 43.1% | 0.9 pp |

La diferencia pareada FQ menos CQ en log-loss ×1000 es −1.3, IC95
[−1.7, −0.8]. Añadir BU a FQ aporta −0.5, IC95 [−0.7, −0.2]. La captura de
FQ + BU L3 al 30% coincide con CQ; a 10% y 20% es algo menor, con intervalos
de la diferencia que incluyen cero. La mejora de estimación no implica que
cambien las prioridades ni demuestra utilidad causal de una intervención.

La partición corregida conserva población, capacidad y verdadero REST.
Ningún escenario principal con hijos de 100 personas pasa todas las guardas
en ambos periodos. Sólo pasan las sensibilidades de 150 y 200 para
FQ + BU L3 a capacidad 10%; esto no respalda una subdivisión general.
Los padres no priorizados permanecen intactos y ningún padre se duplica con
sus hijos. El resultado supersede la interpretación del residual de la
subdivisión selectiva anterior, no los artefactos históricos.

El sesgo de enero–febrero activa el contraste del escalar R6 en los tres
modelos. La corrección aprendida con tres orígenes anteriores empeora sesgo
absoluto y log-loss posteriores: no se recomienda. Agosto–diciembre no activa
la etapa. La disponibilidad QVoice completa/parcial/ausente se analiza por
capacidad frente a la base RH en las mismas cohortes; ausencia no equivale
a retorno automático a RH. Enero coincide con cambios de encuesta y ajuste.

Las tasas observadas usan IC95 de 500 remuestreos por persona compartidos
entre modelos; el riesgo medio usa un intervalo aproximado por gradiente y
covarianza agrupada de las dos etapas. No son intervalos de predicción
individual. Se distinguen personas, persona-mes, personas con evento y
salidas únicas persona-fecha; las ventanas se superponen.

Persisten dos límites temporales: IOS en C/CQ histórico carece de
acreditación de publicación histórica y la política anual de QVoice no
acredita la fecha real de publicación. Los modelos se entrenan con etiquetas
anteriores al origen, pero no se declara disponibilidad histórica completa
de todas las features. Antes de un piloto se necesita resolver esos límites,
confirmar responsables/capacidad y evaluar una cohorte posterior al ajuste.

La primera entrega documental se guardó antes del cálculo. Se completaron
cuatro ajustes principales RH y cuatro Q; los nueve orígenes auxiliares R6
implicaron otros nueve ajustes por etapa. Un suplemento leyó las fechas de
evaluación para completar cruces faltantes, reutilizando los seis modelos
sin ajustes. Esta lectura adicional se registra como desviación del objetivo
de una sola carga compartida. No se persistieron filas ni scores individuales.

- [Resumen de la revisión para RH](../../output/analysis/engineering/20261012/julia-rh-review-v1/resumen-julia-rh.md).
- [Informe](../../output/analysis/engineering/20261012/julia-rh-review-v1/informe.md), [diagnósticos completos](../../output/analysis/engineering/20261012/julia-rh-review-v1/diagnosticos-completos.md) y [fichas](../../output/analysis/engineering/20261012/julia-rh-review-v1/fichas/indice.md).
- [44 filas en Excel](../../output/analysis/engineering/20261012/julia-rh-review-v1/documentacion/variables-44.xlsx) y [tabla final](../../output/analysis/engineering/20261012/julia-rh-review-v1/documentacion/variables-44-final.md).
- [Resultados y SQL trazable](../../output/analysis/engineering/20261012/julia-rh-review-v1/results.json), [anexo técnico](../../output/analysis/engineering/20261012/julia-rh-review-v1/anexo-tecnico.md) y [verificación](../../output/analysis/engineering/20261012/julia-rh-review-v1/verification-delivery.json).
- [Presentación corregida](../../output/presentations/20261013-1100_transfer-sensitivity/presentacion-eng.html): conserva las **9 diapositivas**, su orden e inglés. El contenido proyectado sustituye B, C, CQ y FQ por la progresión `Base → Enhanced → Enhanced + QVoice`; `Selected` se muestra como estado separado. Los códigos internos permanecen en la evidencia técnica. El slide 4 conserva las ocho comprobaciones en lenguaje para RH y el slide 8 nombra las pruebas posteriores por BU L3, work city, combinación y sensibilidad de retirar Transfers. No cambian cifras previas, periodos, variantes, grupos ni la selección de CQ. La expansión de 16 se conserva sólo como historial.
- [Ampliación C + BU con/sin QVoice](c-bu-isolation-20261013.md): C + BU sin encuesta mejora pérdidas frente a C, pero no supera a CQ; ciudad y QVoice aportan mejora adicional. Incluye la guía de 44 variables con roles añadidos para esas variantes.

SQL adicional guardado en `queries/audits/julia_review_unique_events_20261012.sql`
y `queries/audits/julia_review_unique_group_events_20261012.sql`; población y
join en `queries/profiles/engineering_bu_l3_person_month_20261012.sql` y
auditorías BU. Fechas, hashes y resultados agregados en `input-evidence/`.
