# Procedural Justice in Algorithmic Fairness: Leveraging Transparency and Outcome Control for Fair Algorithmic Mediation

## Ficha

- **Autores:** Min Kyung Lee, Anuraag Jain, Hae Jin Cha, Shashank Ojha y Daniel Kusbit
- **Año:** 2019
- **Revista/conferencia:** *Proceedings of the ACM on Human-Computer Interaction*, 3(CSCW), artículo 182, 26 páginas
- **DOI:** `10.1145/3359284`
- **URL oficial:** https://doi.org/10.1145/3359284
- **Fuentes consultadas:** copia pública alojada por UT Austin, Crossref y Semantic Scholar
- **Fecha de consulta:** 2026-09-24
- **Estado de acceso:** Bronze/editorial; PDF autoral público consultado, licencia de redistribución no verificada
- **Etiquetas:** `gobierno`, `fairness`, `procedural-justice`, `transparency`, `contestability`, `human-review`

## Abstract y resumen

### Resumen en español

El paper propone un marco de justicia procedimental para decisiones
algorítmicas. Distingue transparencia de estándares, explicación de resultados y
control del resultado, y añade principios transversales de consistencia,
competencia, benevolencia y voz. Como caso de estudio implementa una interfaz
para dividir bienes con Spliddit, mostrando reglas, entradas y salidas y
permitiendo que el grupo ajuste el resultado.

En un estudio de laboratorio within-subjects participaron 71 personas en 23
grupos de dos a siete. La claridad de estándares por sí sola no aumentó la
percepción de fairness; la explicación de resultados tuvo efectos mixtos y pudo
desplazar la atribución de responsabilidad desde el algoritmo hacia los
participantes. El control del resultado mejoró universalmente la percepción de
fairness después de permitir explorar alternativas; 22% de los grupos cambió su
resultado final. Es evidencia sobre diseño y aceptación de procedimientos, no
sobre predicción de attrition ni sobre HR.

## Pregunta y datos

- **Pregunta:** ¿cómo hacer que una decisión algorítmica sea percibida como procedimentalmente justa?
- **Población:** participantes de un estudio de laboratorio que dividieron alimentos en grupos; no empleados
- **Tamaño:** 71 participantes, 23 sesiones/grupos
- **Grain:** participante dentro de una decisión grupal de una sola ocasión
- **Target y horizonte:** percepción de fairness de la asignación; sin horizonte longitudinal
- **Censura o competing risks:** no aplica

## Método y validación

- **Método:** diseño within-subjects con fases baseline, transparencia y control del resultado; interfaz de fair division y entrevistas semiestructuradas
- **Variables:** ratings de fairness en escala Likert de 7 puntos, entradas y resultados de la asignación, cambios individuales/grupales y temas cualitativos
- **Split temporal:** no; decisión única en laboratorio
- **Métricas:** medias y errores estándar de fairness; análisis cualitativo bottom-up de entrevistas por dos investigadores; 22 conceptos se sintetizaron en 11 categorías
- **Resultados:** la transparencia de estándares no bastó; la explicación de inputs/outputs tuvo efectos mixtos; el control y la discusión elevaron la percepción de fairness, incluso cuando el grupo no cambió el resultado

## Limitaciones

- **Leakage:** no es un modelo predictivo; no aplica como riesgo de datos de Attrition
- **Sesgos:** tarea de baja importancia, grupos pequeños, decisión única, muestra universitaria y contexto de bienes compartidos
- **Generalización:** el propio paper limita la transferencia a otros dominios, decisiones de alto impacto, diseños between-subjects y algoritmos black-box
- **Fairness/privacidad:** la transparencia social completa de inputs y resultados puede ser inapropiada en entornos comerciales; debe equilibrarse con privacidad, seguridad y el riesgo de atribuir injustamente responsabilidad a las personas

## Aplicabilidad a Attrition

- **Relación con Critical Tech:** aporta un marco de gobernanza para que la definición de target, criterios, explicaciones y revisión humana sean explícitos antes de usar un modelo
- **Variables disponibles relacionadas:** ninguna entra como predictor; sí son relevantes los metadatos de definición, fecha de conocimiento, owner, población y reglas de uso del modelo
- **Qué adoptar:** separar claridad de estándares de explicación de resultados, documentar voz/recourse y mantener revisión humana de cualquier acción; reportar resultados de forma agregada
- **Qué probar como challenger:** no aplica como predictor; puede usarse como checklist de aceptación para champion y challengers
- **Qué posponer:** transparencia de filas o explicaciones individuales a managers, automatización de acciones y cualquier uso de atributos protegidos como feature de targeting

## Acción y decisión

- **Señal asociada:** comprensión del procedimiento, oportunidad de voz y posibilidad de corregir o apelar un resultado
- **Palanca potencial:** gobernanza, explicación, contestabilidad y revisión humana
- **Acción candidata:** añadir un gate de documentación y revisión antes de promover un modelo; definir quién puede cuestionar la especificación y cómo se registran las decisiones
- **Métrica de seguimiento:** calibración y desempeño out-of-time, estabilidad, auditoría agregada autorizada y trazabilidad de decisiones; no una única cifra de fairness
- **Decisión:** `referencia conceptual` y `gobierno adoptado`

## Trazabilidad

- **Evidencia consultada:** PDF público del autor en UT Austin `https://pages.ischool.utexas.edu/hai-files/files/publications/45/2019-CSCW-Al_ProceduralFairness.pdf`; Crossref `https://api.crossref.org/works/10.1145%2F3359284`; Semantic Scholar `https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/3359284`
- **Sección/página si el texto completo fue revisado:** abstract, marco de justicia procedimental (pp. 3–7), método y medidas (pp. 10–13), resultados (pp. 13–18) y limitaciones (p. 21–22)
- **Limitaciones de acceso:** se consultó una copia pública alojada por la universidad; ACM clasifica el acceso como bronze y no se asume una licencia de redistribución
