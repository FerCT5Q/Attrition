# Alcance de B + candidatas del playbook V11

Modo `presentation`. Preparación congelada el 12-oct-2026. Este documento describe el alcance; las mejoras predictivas se publican en el informe de resultados.

Se conservan los ocho predictores y las dos interacciones de B. Se prepararon 41 candidatas RH y 51 QVoice. Las preguntas comunes de QVoice se prueban individualmente y los aliases no se cuentan dos veces.

La referencia es `output/distribution/attrition-43-variable-distributions-v11.html`, SHA256 `24ce87b431406f1e1dd2ebde452b1cb739ee1231c53227fa5a3282d5af6e5b5f`.

El nombre «43 variables» identifica el playbook. Su revisión actual tiene 42 vistas analíticas; varias contienen preguntas, cruces o representaciones distintas de un concepto. Por ello el total de candidatas no es el número de vistas.

| Slide | Vista | Prioritaria | Preparación | Candidatas o términos de B | Alcance y limitación |
|---:|---|---|---|---|---|
| 3 | Movimientos IOS | Sí | No seleccionable | — | Los seis motivos existen descriptivamente, pero sus cargas actuales no acreditan conocimiento histórico. Se retira también ios_12m; B no contiene IOS. |
| 4 | Región y mercado laboral | Sí | Preparada | Región, País laboral, Mercado laboral registrado | Se prueban por separado región, país y mercado registrado en la propia foto. |
| 5 | Modalidad de trabajo | Sí | Preparada | Modalidad de trabajo, Modalidad en tres grupos del V11 | Se contrasta la agrupación anterior con los tres grupos exactos del V11, incluido Short-Term Remote Work. |
| 6 | Engineering y otras funciones | Sí | Constante | — | Engineering define la población de esta ronda; no discrimina dentro de ella. |
| 7 | Recontratación | Sí | Obligatoria en B | rehire | Se conserva la variable de B. |
| 8 | Adquisiciones | Sí | Preparada | Adquisición registrada, Adquisición registrada: detalle | Se prueba presencia y detalle registrado; sin registro no demuestra contratación orgánica. |
| 9 | Experiencia previa | Sí | Preparada | Experiencia previa | Se conservan las bandas y desconocidos de la fuente histórica. |
| 10 | Distancia estimada | Sí | Preparada con limitación | Aproximación postal a oficinas de la ciudad (Onsite) | Aproximación postal a oficinas de la ciudad para Onsite. Mapping público estático; distancia mínima cuando hay varias oficinas. No es commute real validado. |
| 11 | Temas de retención en comentarios QVoice | Sí | Preparada | QVoice: presencia de comentario de mejora, QVoice: comentario sobre recompensas, QVoice: comentario sobre carrera y promoción, QVoice: comentario sobre manager, liderazgo y respeto, QVoice: comentario sobre carga de trabajo y equilibrio personal, QVoice: comentario sobre modalidad y traslado, QVoice: comentario sobre herramientas, procesos y burocracia, QVoice: comentario sobre confianza y estabilidad laboral | Se incorporan los siete temas de la taxonomía completa y presencia de comentario de mejora, con waves 2024/2025 y desfase anual. |
| 12 | Intención de permanecer: preguntas | Sí | Preparada | QVoice: permanecer en Qualcomm (Q4), QVoice: poca intención de buscar otro empleo (Q12) | Cada pregunta se prueba separada; los aliases Q4/Q12 no duplican variables. |
| 13 | Metas profesionales | Sí | Preparada con limitación | QVoice: alcanzar metas de carrera | Se mantiene la limitación de cambio de redacción en 2024. |
| 14 | Promedio de preguntas comparables QVoice | Sí | Preparada | QVoice: promedio de 33 preguntas, QVoice: disponibilidad de respuestas, QVoice: promedio relativo a la región | Promedio de 33 ítems comunes, sus 33 pruebas individuales y controles de disponibilidad. La media relativa es respecto a la región contemporánea. |
| 15 | Tiempo en nivel, perfil y rol | Sí | Preparada con historia corta | Tiempo en nivel, Tiempo en perfil de puesto, Tiempo en rol almacenado: bandas V11 | Tres medidas distintas. Perfil aparece en noviembre de 2025 y rol almacenado en agosto de 2025; cada corte exige seis fotos observables. La fórmula de rol no se declara confirmada. |
| 16 | Antigüedad en Qualcomm | Sí | Obligatoria en B | tenure_playbook_band | Se conservan las seis bandas de B. |
| 17 | Tiempo desde la última promoción | Sí | Obligatoria en B | time_since_promotion_band, Entrada observada al grado actual, Tiempo desde entrada observada al grado | B conserva su promoción. Las incorporaciones contrastan la entrada observada al grado dentro del episodio, sin afirmar contratación directa. |
| 18 | Promoción y salidas por track | Sí | Parcial | time_since_promotion_band, Prefijo de grado, Grado de compensación detallado, Track de compensación | Track y grado se prueban; el flag promotion_yes_no de Annual Review queda fuera por falta de publicación histórica verificada. No se equipara a is_promo. |
| 19 | Capas de la jerarquía | Sí | Preparada con límite semántico | Capa organizacional registrada, Profundidad jerárquica reconstruida | Se comparan capa almacenada y profundidad reconstruida en la misma foto; una raíz no se denomina CEO sin validación de negocio. |
| 20 | Tamaño del equipo directo | Sí | Obligatoria en B | direct_reports_band | Se conserva el tamaño directo de B; no se confunde con el equipo del manager. |
| 21 | Compa-ratio | Sí | Preparada con límite semántico | Banda de compa-ratio registrado | Bandas de la razón almacenada; no se afirma que su fórmula de origen esté validada. |
| 22 | Salidas recientes bajo el manager actual | Sí | Preparada | Salidas del equipo en 6 meses, team_exits_12m, Salidas bajo el manager actual, 6 intervalos | Se distingue el contexto de compañeros de B del conteo V11 bajo el manager actual. Seis intervalos completos después del inicio del feed. |
| 23 | Salida del manager | Sí | Preparada | Salida previa del manager | Salida anterior a la foto, con evento conocido y episodio vigente. |
| 24 | Solicitudes de empleo | No | No seleccionable | — | applications termina en octubre de 2024. La vista alternativa tiene eventos recientes, pero falta historial del vínculo y observabilidad. Ausencia de feed no equivale a cero solicitudes. |
| 25 | Ubicación laboral | No | Preparada | País laboral, Sitio laboral, Ciudad laboral | País, sitio y ciudad de la foto; no se usan domicilios como categorías. |
| 26 | Sitio y ciudad de oficina | No | Preparada | Sitio laboral, Ciudad laboral | Se incorpora ciudad; algunos códigos de sitio representan varias ciudades. |
| 27 | Salidas anteriores del equipo | No | Preparada | Salidas del equipo en 3 meses, Salidas del equipo en 6 meses, Recencia de salidas del equipo | El estudio por evento orienta la hipótesis; sólo se usan salidas conocidas antes de t. |
| 28 | Sensibilidad: equipos de seis o más | No | Contexto | Tamaño del equipo del manager, Intensidad de salidas del equipo | El umbral de equipo es una sensibilidad del estudio; tamaño e intensidad se prueban como representaciones adicionales. |
| 29 | Familia de puesto | No | Preparada | Familia de puesto detallada, Grupo de familia de puesto | Detalle y grupo se prueban por separado; categorías raras se agrupan sólo con entrenamiento. |
| 30 | Género | No | Fuera de autorización | — | Atributo protegido excluido de la autorización de predicción; no se usa como feature. |
| 31 | Comentarios sobre modalidad | No | Preparada | QVoice: presencia de algún comentario, QVoice: mención de trabajo remoto, QVoice: mención de trabajo híbrido, QVoice: mención de asistencia a oficina, QVoice: petición de flexibilidad remota o híbrida, QVoice: inquietud de política presencial | Presencia, menciones y peticiones se prueban por separado. No comentario, no enlace y ausencia de pregunta son distintos; mención no demuestra sentimiento. |
| 32 | Heartbeat de QVoice | No | No seleccionable | — | 2024 no tiene escalas ordinales; 2025 tiene 52 de 53 y falta Q42. No se cambia el denominador ni se adelanta la wave 2026, asignada a 2027. |
| 33 | Nivel | No | Obligatoria en B | level_grouped | Se conserva el nivel de B. |
| 34 | Familia de grado | No | Preparada | Prefijo de grado, Grado de compensación detallado, Track de compensación | Se prueban prefijo de grado, código completo y track V11 por separado. |
| 35 | Grados en las capas 0–2 | No | Contexto | Profundidad jerárquica reconstruida, Grado de compensación detallado | Es un cruce descriptivo; usa las mismas representaciones de jerarquía y grado, sin duplicarlas. |
| 36 | Grado de compensación | No | Preparada | Grado de compensación detallado | Se usa el código, sin importes individuales. |
| 37 | Compensación relativa dentro del equipo | No | Preparada | Posición salarial relativa en grupo comparable, Dispersión salarial en equipos comparables | Pares comparables de país, grado y moneda. Recálculo independiente; ningún importe sale de SQL. |
| 38 | Diferencia horaria con el manager | No | Preparada con limitación | Relación horaria con el manager | Catálogo público estático y offsets de cada foto con DST, verificados en 1,036 casos. No se acredita vigencia histórica de direcciones. |
| 39 | Coincidencia de ubicación con el manager | No | Preparada | Ubicación respecto al manager, Coincidencia de sitio y ciudad con el manager | Se contrasta relación país/sitio/ciudad con coincidencia V11 de sitio y ciudad. Registro igual no demuestra proximidad física. |
| 40 | Salidas observadas y esperadas del manager | No | Preparada | Salidas observadas/esperadas del manager, 6 intervalos | Ratio con exposición histórica, benchmark por estratos y seis intervalos completos; no es una calificación del manager. |
| 41 | Salidas del manager sobre el benchmark | No | Preparada | Salidas sobre benchmark del manager, 18 intervalos | Dieciocho intervalos completos, equipo promedio de al menos cuatro, dos salidas y umbral 1.3 veces el benchmark; historia desde abril de 2024. |
| 42 | Cambio de manager | No | Obligatoria en B | manager_changes_12m | La presencia del evento está contenida en el conteo obligatorio de B. |
| 43 | Cantidad y recencia de cambios de manager | No | Preparada | manager_changes_12m, Cambios de manager en 3 meses, Cambios de manager en 6 meses | B conserva doce meses y se contrastan tres y seis meses. Las definiciones de grupo no se fuerzan a 22. |
| 44 | Talent index | No | No seleccionable | — | La metadata actual sólo contiene timestamps técnicos en master_talent_index; no hay fecha de negocio ni snapshot del índice para un enlace as-of. |

Preparada significa que existe una representación reproducible; cada corte todavía exige historia suficiente. No seleccionable describe una brecha de datos, no falta de utilidad predictiva. No se cambian scores de assessment.

Los periodos externos, controles y comparaciones finales se guardan en `informe.md`, `comparacion-variables.csv` y `results.json` de esta misma carpeta al terminar la ejecución.
