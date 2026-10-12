# Correspondencia del playbook V11 con la ronda B + X

Modo `presentation`. Referencia señalada expresamente por el usuario. Esta tabla identifica brechas de implementación; no asigna scores de assessment.

| Slide | Vista del playbook | Prioritaria | Estado en la ronda interrumpida | Acción |
|---:|---|---|---|---|
| 3 | IOS movement events | Sí | parcial | Desglosar los seis motivos del playbook, permitiendo solapamientos. |
| 4 | Region | Sí | parcial | Incorporar mercado laboral; no confundir región con mercado. |
| 5 | Work arrangement | Sí | parcial | Contrastar la agrupación V11 de tres modalidades con la agrupación usada por C. |
| 6 | Engineering vs. non-engineering | Sí | constante | Engineering ya define la población; no discrimina dentro de ella. |
| 7 | Rehire | Sí | B | Conservar el indicador de B. |
| 8 | Acquisitions and attrition | Sí | parcial | Probar la categoría de adquisición; sin registro no acredita contratación orgánica. |
| 9 | Experience before Qualcomm | Sí | incluida | Conservar las bandas de experiencia previa y su cobertura histórica. |
| 10 | Estimated commute distance and voluntary attrition | Sí | preparación existente por incorporar | Revisar la preparación geográfica y su vigencia histórica; derivar únicamente bandas en RAM. |
| 11 | Retention concerns in QVoice comments | Sí | preparación existente por incorporar | Reconstruir temas de comentarios con taxonomía congelada y waves anteriores al año predicho. |
| 12 | Intent to Stay items | Sí | incluida | Intent to Stay: las preguntas se prueban por separado; aliases contados una sola vez. |
| 13 | Career goals item | Sí | incluida | Mantener la limitación de cambio de redacción en 2024. |
| 14 | Average of comparable QVoice items | Sí | incluida | Promedio de los 33 ítems comunes; no es el promedio de todas las preguntas de cada wave. |
| 15 | Time at detailed level and time in role | Sí | parcial | Revisar el tiempo en rol y el tiempo en nivel exactos; no equiparar etiquetas. |
| 16 | Company tenure | Sí | B | Conservar las seis bandas de B. |
| 17 | Time since last promotion | Sí | B | Conservar la historia de promoción de B. |
| 18 | Promotion and attrition by pay track | Sí | parcial | La lámina cruza promociones de Annual Review y tasas por track; revisar fecha de conocimiento y entrada al grado, sin asumir equivalencia. |
| 19 | Manager layers to the CEO | Sí | parcial | V11 tiene reconstrucción de jerarquía; el modelo usaba bandas de la capa almacenada. |
| 20 | Direct team size (span) | Sí | B | Conservar el tamaño directo de B; no confundirlo con todo el equipo del manager. |
| 21 | Comp ratio | Sí | incluida | Razón almacenada por bandas; no afirmar validación de la fórmula de origen. |
| 22 | Recent team exits under the current manager | Sí | parcial | Contrastar salidas bajo el manager histórico con la definición de compañeros de las features actuales. |
| 23 | Manager leaving | Sí | incluida | Salida previa del manager; fecha efectiva y conocida antes de t. |
| 24 | Applied to a job | No | preparación existente por revisar | Revisar aplicaciones registradas y enlace. Ausencia de enlace/feed no equivale a cero aplicaciones. |
| 25 | Location | No | parcial | Revisar las vistas de ubicación del playbook; no usar domicilios como categorías. |
| 26 | Office site and city | No | parcial | Añadir ciudad laboral; algunos códigos de sitio representan un país entero. |
| 27 | Does one team departure precede more departures? | No | parcial | El estudio por evento aporta una hipótesis; no se copia su outcome como predictor. |
| 28 | Sensitivity check: teams with 6+ employees | No | contexto | La restricción a equipos de seis o más es una sensibilidad del estudio, no una variable individual adicional. |
| 29 | Job family | No | incluida | Probar detalle y grupo por separado con categorías raras agrupadas sólo en entrenamiento. |
| 30 | Gender | No | excluida | Atributo protegido fuera de la autorización de predicción. |
| 31 | QVoice comments about remote, hybrid, and office work | No | preparación existente por incorporar | Reconstruir flags de temas y presencia de comentario; conservar falta de enlace y no comentario por separado. |
| 32 | QVoice heartbeat | No | limitación temporal por comprobar | El Heartbeat relativo requiere sus preguntas de escala; no sustituirlo por respuestas binarias ni adelantar wave 2026. |
| 33 | Level | No | B | Conservar el nivel de B. |
| 34 | Level grouped by grade family | No | incluida | Se prueban familia y grado; documentar diferencia entre prefijo R/T y todos los tracks válidos. |
| 35 | 0–2 layers: exact compensation grades | No | contexto | El corte de 0–2 capas requiere la jerarquía reconstruida; es un cruce, no una nueva fuente. |
| 36 | Compensation grade | No | incluida | Código completo, sin importes. |
| 37 | Within-team compensation range | No | incluida | El cálculo activo usa pares comparables y recálculo independiente, sin importes fuera de SQL. |
| 38 | Assigned office-site proximity to manager | No | preparación existente por incorporar | Reutilizar mapping de oficinas y zonas horarias, con fecha, DST y desconocidos explícitos. |
| 39 | Office-site relationship with manager | No | parcial | Contrastar categorías de sitio exactas de V11 con la representación ampliada sitio/ciudad/país. |
| 40 | Manager observed-to-expected exit ratio | No | preparación existente por incorporar | El ratio observado/esperado tiene definición independiente: recalcular historia conocida, estratos y suavizado. |
| 41 | Above-average team turnover | No | preparación existente por incorporar | Flag de 18 intervalos con observabilidad y benchmark; no es la intensidad de salidas de 12 meses. |
| 42 | Manager change | No | B | La existencia de un evento está representada por el conteo de B. |
| 43 | Number of manager changes | No | parcial | Revisar las definiciones de evento del playbook; conservar términos de B. |
| 44 | Talent index | No | limitación temporal documentada | La fecha efectiva/publicación del Talent index no está confirmada; revalidar metadata antes de decidir. |
