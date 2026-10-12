# Qué probar después de C + QVoice

Revisión: **10-oct-2026**. Clasificación: `presentation`.
Objetivo: identificar grupos con mayor attrition, estimar bien su riesgo y mantener reglas que permitan orientar acciones.

## Recomendación

**Mantendría C + QVoice (`CQ`) como modelo elegido en esta etapa y abriría una ronda acotada de mejoras.** Hay alternativas pendientes, especialmente el ajuste conjunto de C y QVoice, interacciones interpretables, historia de los eventos y Random Survival Forest con QVoice. La literatura respalda investigarlas; su superioridad requiere una comparación local.

Mi primera prueba sería **reajustar C y QVoice conjuntamente**, comparándolo con C actualizado y con la corrección Q actual bajo las mismas fechas. Después probaría unas pocas interacciones entre carrera, intención de permanencia y contexto laboral. La precisión y estabilidad de los grupos prioritarios deben formar parte de la selección desde el principio.

La revisión comprende las **43 fichas del inventario oficial** y su trazabilidad, los dos playbooks y los informes, configuraciones, resultados agregados y partes pertinentes del código de los modelos. El inventario contiene **42 trabajos revisados previamente y un candidato, P31, limitado a metadatos**. Parte de las fichas se apoya sólo en abstracts. Esta revisión no equivale a una nueva lectura íntegra de 43 originales. El alcance por trabajo está en la [matriz de los 43 papers](matriz-43-papers.md).

## 1. Qué sostiene actualmente la elección

Modelo vigente: `engineering-c-qvoice-20261008-v1`, confirmado el 10-oct-2026 en el [registro de selección](../../../../../docs/context/model-selection-current.md). Es un hazard mensual cloglog con C como base fija y una corrección QVoice. El riesgo a seis meses se acumula como `R6 = 1 − producto(1 − h_m)`.

### C frente a CQ en la comparación más reciente

Fotos de **agosto–diciembre de 2025 y enero–febrero de 2026**, cada una con seguimiento de seis meses. Igual peso para ambos periodos. Población: Engineering, Employee, Regular, activo, sin RF360. Las unidades son persona-foto; personas y ventanas se repiten.

| Medida | C | CQ | Lectura |
|---|---:|---:|---|
| Captura al priorizar el 30% | 42.4% | 43.1% | CQ concentra 0.7 pp más de las salidas observadas |
| Log-loss de R6 × 1000 | 138.8 | 137.7 | CQ reduce la pérdida 0.8% |
| PR-AUC | 4.9% | 5.5% | Mejor separación individual en CQ |
| Error absoluto de grupo-mes en la prioridad | 1 pp | 1 pp | CQ mejora 2.3%; el redondeo oculta esta diferencia pequeña |
| Promedio del mayor error de grupo publicable | 2.1 pp | 2.2 pp | Hay grupos concretos peor estimados con CQ |
| R6 estimado en el 30% prioritario | 5.2% | 5.1% | Ambos sobreestiman el riesgo de sus prioridades |
| R6 observado en el 30% prioritario | 4.5% | 4.6% | Cada modelo puede priorizar personas distintas |

Fuente: [resultados del 9-oct](../../20261009/c-qvoice-mean28-v1/results.json), campos `summary.C`, `summary.CQ` e `intervals`; SQL `queries/profiles/engineering_c_qvoice_mean28_person_month_20261009.sql`, ejecutada el 9-oct-2026. Frontera de conocimiento: 7-sep-2026; último outcome: 22-ago-2026. El IC95 del aumento de captura al 30% es [0.2, 1.2] pp en esta ejecución. Es un intervalo condicionado a los modelos y selecciones explorados; no corrige toda la búsqueda histórica.

CQ gana captura en el periodo de 2025 y empata en enero–febrero de 2026. Al 20% y 40%, los intervalos de mejora de captura incluyen cero. Las ocho métricas correlacionadas no constituyen ocho pruebas independientes.

### Otros modelos conservan ventajas relevantes

El [informe RSF](../../20261008/random-survival-forest-v1/informe.md) compara las versiones disponibles en esos mismos dos periodos:

| Versión disponible | Captura al 30% | Error de grupo-mes | Log-loss × 1000 |
|---|---:|---:|---:|
| B | 41.6% | 0.8 pp | 138.7 |
| C | 42.4% | 1 pp | 138.8 |
| CQ | 43.1% | 1 pp | 137.7 |
| B + Q sin calibración posterior | 43.1% | 0.7 pp | 137.3 |
| RSF sin Q, sin calibración posterior | 42.5% | 0.7 pp | 137.7 |
| RSF sin Q, calibrado | 42.5% | 0.6 pp | 137.6 |

**CQ no domina todas las métricas de todos los modelos.** BQ es prácticamente igual en captura y obtiene menor error; RSF ofrece mejor precisión reciente con menor captura. Hay dos límites para interpretar esa tabla:

- En enero de 2026, RSF tiene ajuste de enero, mientras las bases B/C conservan agosto de 2025. Las correcciones Q tienen sus propias fechas. Parte de la diferencia podría proceder de la actualización.
- BQ conserva un contrato histórico distinto para salidas del equipo: fecha efectiva y frontera global, frente a la exigencia de C/RSF de que el evento ya estuviera registrado en la foto. La reconciliación alinea personas y evalúa todos con la etiqueta de C; una etiqueta entre 238451 observaciones difiere del contrato original de BQ. Alinear etiquetas no elimina la diferencia temporal de los predictores.

Fuente: `qvoice-results.json`, `bq-input-reconciliation.json` y `bq-label-contract-audit.json` del run RSF; SQL `queries/profiles/engineering_rsf_person_month_20261008.sql` y SQL histórica BQ `queries/profiles/engineering_qvoice_horizon_calibration_20261008.sql`; ejecuciones 8–9-oct-2026, misma población indicada arriba. La tabla sirve para identificar candidatos competitivos, sin declarar una superioridad aislada de la familia estadística.

## 2. Familias cubiertas y alternativas pendientes

| Modelo o método | Evidencia local | Prioridad y motivo |
|---|---|---|
| Hazard mensual cloglog, B y C | Implementado; C usa selección supervisada L1 y refit L2 | Conservar como base interpretable; P02–P04 y P11 apoyan el planteamiento temporal |
| BQ y CQ; combinaciones Q; PCA | Implementados. CQ exploró 255 subconjuntos de ocho bloques, cinco tamaños PCA y tres penalizaciones por corte | La búsqueda fue amplia dentro de ese catálogo, pero no incluyó toda representación, interacción o algoritmo posible |
| Logística directa a seis meses | Implementada antes de C/Q | Ya existe; no es el mismo experimento que cambiar sólo el enlace del hazard mensual |
| LightGBM directo a seis meses | Implementado antes de C/Q; también una comparación con más variables | Ya existe. Los resultados antiguos no demuestran qué haría con C/Q y grupos actuales |
| Random Survival Forest sin Q | Implementado; rejilla acotada y distintas agrupaciones | Competitivo. Su calibración empeoró el promedio de cuatro periodos, aunque mejoró los periodos recientes |
| **Hazard C + Q ajustado conjuntamente** | No encontrado en los experimentos revisados: CQ usa C como offset fijo | **Alta**. Permite redistribuir los efectos entre información HR y Q |
| **Hazard con interacciones Q × contexto e historia de eventos** | No encontrado como variante CQ evaluada | **Alta**. Puede distinguir grupos que comparten una respuesta Q pero tienen trayectorias diferentes |
| **RSF + QVoice** | El bosque archivado no incorpora Q | **Alta entre nuevos algoritmos**. Comprueba si las interacciones automáticas aportan valor adicional |
| Boosting del hazard mensual + Q | No encontrado. LightGBM previo predice R6 directamente | Media. Aprovecha etiquetas mensuales maduras; exige revisar calibración, exposición y explicación de grupos |
| Modelo aditivo con curvas suaves, tipo GAM | No encontrado | Media. Posible forma interpretable de flexibilizar antigüedad y tiempos; propuesta de diseño, no ganador demostrado por estos papers |
| Hazard multinivel con efectos parcialmente compartidos | No encontré una evaluación específica | Media, si quedan diferencias persistentes entre cohortes/equipos. P19 motiva estudiar contexto compartido; permite suavizar estimaciones en lugar de ajustar cada grupo aisladamente |
| Hazard mensual con logit | No encontrado como comparación equivalente a CQ | Control de bajo alcance. Ambos enlaces producen probabilidades mensuales; sólo cambia la relación entre predictores y hazard |
| Cox con covariables temporales | No encontrado como modelo local evaluado | Benchmark secundario, P01/P09. No hay evidencia de que sustituir cloglog por Cox vaya a mejorar los grupos |
| Riesgos competidores / estados múltiples | No hay un modelo explícito de causas competidoras | Revisión metodológica prioritaria; implementación condicionada al outcome que se quiera estimar. P05/P07/P09 |
| DeepHit, DeepSurv o redes de secuencia | No encontrados | Baja ahora. DeepHit sí está en P10; DeepSurv y secuencias requerirían ampliar la revisión específica. Más complejidad y poca evidencia local |
| Texto, grafos, modelos de efecto de intervenciones | No implementados como candidatos comparables | Posteriores. P12/P38 no demuestran una mejora aplicable hoy ni renuncias evitadas |

La ausencia significa **“no encontré una implementación evaluada en el material revisado”**. La comparación logística/LightGBM está en [rolling v2](../../20261001/model-comparison-rolling-v2-sin-manager/comparison-report.md); las interacciones HR, tendencia y recalibración previas están en [hazard adjustment v2](../../20261001/hazard-adjustment-v2/adjustment-report.md). P08 y P32 no son dos algoritmos que hayamos replicado: se probó RSF general, sin reproducir específicamente RFRSF de P32.

## 3. Lo que aportan los playbooks

Se revisaron [v11](../../../../distribution/attrition-43-variable-distributions-v11.html) y la [versión anual de Julia](../../../../../docs/julia/attrition-variable-playbook-annual-v1.html). Las comparaciones anuales, YTD y de distintas poblaciones generan hipótesis. Sus tasas no se trasladan directamente al R6 de Engineering.

| Señal del playbook | Qué representa el modelo actual | Mejora que merece prueba |
|---|---|---|
| Intent to Stay, Q4 y Q12; slide 23 | Bloques candidatos con términos propios en cortes históricos; en el final de septiembre ambas entran dentro del promedio de 33 | Interacciones acotadas con carrera, antigüedad y salidas recientes del equipo; medir aporte incremental de cada pregunta |
| Career Goals; slide 24 | Presente en los tres cortes CQ documentados | Career × tiempo sin promoción y Career × antigüedad; comprobar si cambia dónde conviene priorizar |
| Media Q y heartbeat; slides 25–26 | Media de 33 y otras representaciones ya exploradas; PCA no elegido | Mantener constructos interpretables; una respuesta relativa a la media personal no equivale a respuesta desfavorable absoluta |
| Salidas del equipo; slides 9–10 y 45 | Conteo 0/1/2+ en doce meses | Recencia, ventanas de distinta duración y tasa contextual con denominador histórico coherente y suavizado |
| Cambios de manager; slides 48–49 | Conteo de doce meses; algunas interacciones HR ya existían en B | Tiempo desde el último cambio, concentración de cambios recientes y contexto Q; separar cambios coincidentes con movilidad |
| Antigüedad, tiempo en nivel y promoción; slides 29, 31–32 | Bandas y nivel × antigüedad | Curvas suaves, efectos por etapa y actualización mecánica de duraciones al proyectar |
| Span reconstruido; slide 37 de seguimiento | C lee `reg_non_intern_dir_reports` almacenado para `direct_reports_band` | Contrastar con el span reconstruido del manager al que pertenece cada persona. La consulta actual no implementa ese cálculo del playbook |
| Adquisición | Está en C y se probó como corte adicional | Conservarla como contexto; la búsqueda de cortes ya mostró una ganancia modesta. No asumir una nueva ganancia por repetirla |
| Relación de oficina con manager; slides 42–43 | El inventario C la deja pendiente | Candidato posterior sujeto a contrato histórico. Es proximidad de oficina asignada, sin inferir domicilio o presencia real |
| Compensación relativa; slides 39–40 | Bandas de comp-ratio; el inventario distingue dispersión comparable dentro del equipo | Investigar sólo si el contrato comparable y el aporte incremental justifican el trabajo; una diferencia de rango no demuestra inequidad |

### Dos ejemplos concretos de señal y sus límites

En la cohorte QVoice 2025 del playbook, Q4 muestra **11.1%** de attrition anual en respuestas no favorables frente a **2.8%** en favorables. Career Goals muestra **9%** frente a **3.3%**. Son asociaciones fuertes en esas cohortes; no prueban que forzar términos adicionales mejore CQ después de incluir los predictores actuales.

Fuente: slides 23–24 y `output/distribution/json/qvoice-favorable-unfavorable-question-attrition-evidence-20260923.json`, generado el 23-sep-2026; consulta guardada `queries/audits/qvoice_favorable_unfavorable_attrition_window_audit_20260921.sql`. Población: respondentes enlazados a Employee/Regular activos en la foto previa a la encuesta; respuestas válidas de cada ítem, con denominadores propios. Outcome 2025: salidas voluntarias estrictas en los doce meses posteriores al inicio de la encuesta. No es la población/ventana R6 del modelo.

La política vigente asigna **QVoice 2024 a 2025, QVoice 2025 a 2026 y QVoice 2026 a 2027**. Por ello los gráficos descriptivos de la wave 2026 no justifican utilizar esas respuestas en modelos de 2026. Pueden orientar una hipótesis para una prueba posterior que respete esa política.

El inventario de C registra representaciones parciales y variables pendientes. Esta revisión compara implementaciones documentadas; no renueva los scores de las 43 variables ni acredita disponibilidad, equivalencia semántica o cobertura actual de candidatos nuevos. Esas comprobaciones deben realizarse mediante los skills y la evidencia exigidos por el proyecto antes de incorporarlos.

## 4. Ronda de experimentos recomendada

El orden indica el siguiente trabajo útil, no una promesa de mejora. Los costes son relativos de implementación y cómputo; no son estimaciones de disponibilidad de datos.

### E0. Hacer una comparación coherente de las versiones

**Primero:** mismos orígenes de ajuste, población, episodios, fechas de conocimiento, definición de salidas del equipo, horizonte y políticas Q. Conservar B, BQ, C, CQ y RSF archivados como referencias y crear versiones nuevas para los ajustes necesarios.

Esto permite distinguir la mejora por actualizar el modelo de la mejora por añadir QVoice o cambiar de algoritmo. También resuelve la limitación que hoy afecta la comparación BQ/CQ. Coste: bajo–medio, según la carga; reutilizar la extracción compatible en memoria.

### E1. Ajustar C + Q de forma conjunta — primera prueba

Comparar cuatro brazos: CQ archivado, C reajustado, C reajustado con corrección Q como offset y C/Q ajustados conjuntamente. En las variantes nuevas usar los mismos orígenes e información. Seleccionar regularización dentro del entrenamiento, con penalización diferenciada para bloques HR y Q si resulta útil.

**Motivo local:** `engineering_model_c_qvoice.py` calcula `eta_C + corrección_Q`; `hazard_base_refits` es cero. La base no puede redistribuir sus coeficientes cuando entra Q. Ajustarla conjuntamente podría mejorar las probabilidades, aunque también aumentar la varianza; hace falta medirlo. Actualizar sólo el intercepto, ya probado, no equivale a este experimento.

Coste: medio. Conservar pocos candidatos al principio. Seleccionar usando R6 y restricciones de captura/error en grupos; el CQ actual elige bloques principalmente por Brier mensual.

### E2. Interacciones interpretables entre Q y contexto

Probar por separado un catálogo breve:

- Career Goals × antigüedad.
- Career Goals × tiempo desde promoción.
- Q4 × salidas previas del equipo.
- Wellbeing × cambios de manager.

Exigir los efectos principales y penalizar las interacciones. P13, P19–P21 y P26–P30 apoyan estudiar moderación y contexto; no establecen el signo ni el beneficio predictivo de estos cruces exactos en Engineering. Las señales del playbook ayudan a formularlos.

Coste: bajo–medio. La combinación ganadora debe conservar una explicación sencilla del grupo. No buscar todas las interacciones de las 43 variables de forma indiscriminada.

### E3. Usar mejor la historia mensual y el contexto del equipo

Comparar conteos de doce meses con recencia y ventanas de tres/seis meses, separando salidas del equipo, cambios de manager y promociones. Añadir una variante de tasa de salidas sobre exposición histórica del equipo, con suavizado para grupos pequeños y membresía fechada. Un mismo conteo no representa la misma intensidad en equipos de distinto tamaño.

Para Q, explorar edad de la wave y cambios entre waves sólo cuando ambas puedan conocerse según la política anual. Quienes tienen dos respuestas forman una población seleccionada; conservar al resto y distinguir ausencia de respuesta de respuesta desfavorable. La edad de la wave puede quedar confundida con el calendario: requiere una comparación específica.

**Proyección:** C/CQ avanzan el mes del calendario y mantienen las demás covariables de la foto al calcular R6. Es un supuesto de proyección documentable. Puede compararse con avanzar duraciones calculables, como antigüedad, bajo un escenario de continuidad. Promociones, cambios de manager y nuevas respuestas futuras no son conocidos; los escenarios deben explicitarlo. El historial conocido hasta una foto sí puede actualizar la predicción en la foto siguiente.

Coste: medio. Apoyo conceptual: P02–P04, P11, P19 y P22; la forma exacta de las nuevas variables es una propuesta para validar localmente.

### E4. Random Survival Forest + QVoice

Probar el bosque con los mismos bloques Q admitidos y compararlo con RSF sin Q, CQ y el mejor hazard de E1/E2. Usar una búsqueda acotada, mismas fechas y grupos comunes. Publicar versiones cruda y calibrada si se ensaya calibración.

**Motivo local:** RSF ya mostró precisión competitiva sin Q y puede captar interacciones automáticamente. P08 respalda esa capacidad metodológica. La ganancia observada por añadir Q a C no garantiza una ganancia idéntica en RSF.

Coste: medio–alto. Si mejora, medir cuánta captura se conserva al expresarlo con grupos simples; un árbol que explica al bosque es una aproximación y debe evaluarse como tal. Después consideraría boosting mensual con Q como segundo algoritmo adicional.

### E5. Mejorar las reglas de grupos y su precisión

Evaluar primero los mismos cortes para aislar cambios en el estimador. Después aprender agrupaciones específicas del modelo ganador usando exclusivamente datos de entrenamiento y predicciones fuera del ajuste. Penalizar el número de reglas y la inestabilidad de pertenencia/prioridad.

**Ya se hizo trabajo aquí:** se exploraron 3775 cruces de cuatro variables para C; la familia orientada a unos 40 grupos no mejoró la captura al 30%. CQ conserva principalmente cortes por antigüedad, salidas del equipo y nivel. Las sensibilidades posteriores añaden adquisición; no equivalen a una búsqueda completa y temporal de reglas específicas de CQ.

Como ejemplo de la importancia de la política de grupos, `C_four` captura 44.1% en los dos periodos recientes, con error de grupo-mes de 1.1 pp, frente a 43.1% y 1 pp de CQ. Es otra agrupación de las predicciones C, con una historia de selección diferente. No demuestra que exista un estimador C superior a CQ; sí justifica evaluar estimador y reglas de prioridad por separado.

Si persiste sobreestimación en grupos concretos, probar una calibración condicional sencilla con **shrinkage**: ajustes de grupo acercados a un ajuste común para evitar estimaciones extremas. Entrenarla con predicciones temporales fuera del ajuste y contrastar sus resultados con identidad. Las calibraciones de intercepto, pendiente y escalar ya ensayadas impiden presentar “calibrar” como una idea nueva por sí sola.

Una extensión posterior sería un hazard multinivel que incorpore ese contexto compartido durante el ajuste. Su aportación debe medirse también en grupos nuevos, usando el efecto común cuando no exista historia suficiente; no interpretar un efecto de equipo como evaluación causal de su manager.

Coste: medio; se puede reutilizar gran parte del código de agrupación. Mantener mínimos de elegibilidad y publicación. Si una política sólo permite grupos completos, reportar también su capacidad real: el 30% exacto histórico permite peso fraccional uniforme en el grupo del límite.

## 5. Riesgos competidores: una revisión metodológica que sí falta

P05, P07 y P09 distinguen **salida voluntaria**, otras salidas y permanencia. Para probabilidades reales de salida voluntaria, una salida por otra causa elimina la posibilidad de una renuncia posterior dentro del mismo episodio.

La SQL actual crea indicadores de salida voluntaria y completa con cero cuando no encuentra ese evento, siempre que la ventana calendario haya madurado. No estima hazards separados para las demás causas. Antes de cambiar el modelo conviene documentar, por episodio, qué se trata como otra salida, censura o pérdida de observación y comprobar la coherencia entre el ajuste mensual y la etiqueta R6. Esta revisión no cuantificó el impacto de ese tratamiento.

Un modelo mensual de causas competidoras estimaría probabilidades coherentes de cada causa y acumularía la incidencia voluntaria como:

`F_vol(6) = suma_m S_total(m−1) × h_vol(m)`

`S_total(m) = S_total(m−1) × [1 − suma_c h_c(m)]`

Así, `1 − producto(1 − h_vol)` por sí solo no es la incidencia voluntaria observada cuando existen otras causas competidoras explícitas. Cox por causa o Fine–Gray son alternativas con objetivos distintos; no son sustituciones mecánicas de una fórmula.

La movilidad interna puede ser una covariable o un estado intermedio. Sólo sería un evento terminal si la definición de negocio lo exige. Priorizaría esta revisión del target desde E0; el entrenamiento de causas separadas depende de que la distinción resulte material para las decisiones.

## 6. Cómo decidir si una mejora merece sustituir a CQ

1. **Congelar el protocolo antes de ver resultados:** población, fechas, definición de éxito, capacidad principal 30%, sensibilidades 20%/40%, reglas de agrupación y complejidad admisible.
2. **Validación temporal anidada:** aprender columnas, transformaciones, regularización, grupos y calibración sólo en el entrenamiento de cada origen. Todas las etiquetas usadas deben estar maduras y conocidas entonces. Eliminar del ajuste cualquier ventana cuyo desenlace cruce el origen externo.
3. **Medir la decisión:** captura al 30%, riesgo observado de los grupos seleccionados, error absoluto de grupo-mes, sesgo y error del peor grupo con evidencia suficiente. Comparar probabilidades tanto sobre prioridades propias como sobre las mismas personas priorizadas por CQ.
4. **Medir precisión global:** log-loss y Brier R6, además del hazard mensual. Evaluar R1/R3 como secundarios si se usarán; una mejora mensual no garantiza la mejor R6. Si hay censura real, usar una evaluación compatible con ella.
5. **Medir estabilidad e interpretación:** persistencia de los grupos, cambios de orden entre meses, tamaño, cobertura publicable y reglas que permitan plantear un diagnóstico. Aumentar el número de grupos no constituye por sí mismo una mejora.
6. **Mostrar incertidumbre realista:** remuestreo pareado de personas completas, sensibilidad a bloques de calendario y dependencia de equipos cuando sea posible. Las ventanas se solapan; siete fotos no son siete réplicas independientes. Con sólo dos periodos Q la estabilidad temporal sigue limitada.
7. **Usar una regla de promoción conjunta:** exigir mejora material de captura con error prioritario dentro de tolerancia, o captura prácticamente equivalente y una reducción material del error prioritario. Como punto de partida se pueden conservar los límites ya usados de 0.1 pp de empeoramiento en error y 0.5% relativo en pérdidas; son propuestas para fijar antes de ejecutar. Si las diferencias no son claras, preferir la versión más simple y estable.
8. **Separar selección y confirmación:** los periodos ya explorados permiten desarrollo retrospectivo. Reservar nuevos periodos para confirmación cuando maduren sus desenlaces. Con el corte archivado 7-sep-2026, las fotos posteriores a febrero de 2026 no tienen automáticamente seis meses completos; tener una foto nueva no madura R6. Los coeficientes finales de septiembre tampoco heredan la evaluación de sus modelos históricos.

Las reglas de grupos orientan dónde investigar. Una asociación predictiva no demuestra que una promoción, cambio de manager o intervención concreta evite salidas. P06 y P34–P38 refuerzan la necesidad de separar calidad predictiva, explicación y efecto de una acción.

## 7. Qué no priorizaría ahora

- **Repetir más promedios Q por sí solos.** Las variantes fijas media33/media28 no superaron CQ. Media28 reduce el VIF máximo documentado de 4.1 a 3.5, pero no mejora claramente la predicción; la matriz completa también tiene redundancias debidas a ausencia compartida. Una codificación más limpia puede mejorar estabilidad numérica sin aumentar captura.
- **PCA como criterio principal de selección.** Puede usarse con snapshots si se ajusta sólo con entrenamiento y se aplica sin información futura. Maximiza varianza de predictores, no predicción de attrition, y mezcla interpretaciones. CQ ya lo probó sin seleccionarlo. Para este objetivo conviene selección supervisada y penalización por bloques.
- **Deep learning por resultados en IBM/Kaggle.** P41 usa datos sintéticos; P42 predice intención con una encuesta y validación distinta. Ninguno demuestra superioridad sobre nuestro CQ temporal.
- **Texto libre, grafos o contrafactuales presentados como causalidad.** P12/P38 son líneas posteriores. La ficha adicional de supervivencia con grafos, fuera de los 43, usa benchmarks transversales con tiempos proxy. No proporciona una razón suficiente para incorporarla ahora.
- **Un índice global de engagement/embeddedness/voz.** P15–P17, P23–P27 y P43 distinguen constructos y niveles. Promediar preguntas de una persona es distinto de medir contexto entre personas de un equipo; participación en QVoice tampoco equivale a voz o silencio organizacional.

## 8. Fuentes, alcance y estado de la entrega

La [matriz](matriz-43-papers.md) vincula cada paper con una decisión. El [manifest](manifest.json) identifica las fuentes y sus hashes para rastrear esta revisión. Los principales expedientes son:

- `docs/research/attrition-literature/`: matriz oficial, registro de fuentes, síntesis, candidatos y fichas.
- `docs/context/model-selection-current.md`: decisión vigente, que prevalece sobre recomendaciones históricas de mantener C.
- `model-c-v2`, `c-group-selection-v1`, `c-fourway-groups-v1`, `model-c-plus-qvoice-v1`, `random-survival-forest-v1`: runs del 8-oct y sus resultados agregados.
- `c-qvoice-overlap-v1` y `c-qvoice-mean28-v1`: comparaciones del 9-oct.
- Configuraciones y consultas guardadas de C/CQ/RSF; scripts de acumulación R6 y ajuste Q revisados como evidencia de implementación.

Se identificó una discrepancia de autoría en el índice bibliográfico: P36 figura como Green & Hu, mientras su ficha y DOI corresponden a Hanna, Denton, Smart y Smith-Loud. Esta revisión usa la identidad de la ficha/DOI y conserva el índice histórico. P31 mantiene su estado de candidato; no aporta resultados empíricos a las recomendaciones.

Entrega realizada: revisión documental, contraste con agregados existentes y propuesta de experimentos. No se entrenaron modelos, ejecutaron consultas nuevas ni cambiaron parámetros, scores, decisiones de selección o resultados anteriores.
