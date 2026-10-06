# Towards a Critical Race Methodology in Algorithmic Fairness

## Ficha

- Autores: Alex Hanna, Emily Denton, Andrew Smart y Jamila Smith-Loud
- Año: 2020; versión arXiv consultada de 2019
- Conferencia: FAT* 2020, 12 páginas
- DOI: `10.1145/3351095.3372826`
- URL oficial: https://doi.org/10.1145/3351095.3372826
- Fuente consultada: ACM y arXiv, `1912.03593`
- Fecha de consulta: 2026-09-14
- Estado de acceso: Open Access
- Etiquetas: `gobierno`, `fairness`, `measurement`, `referencia-conceptual`

## Abstract y resumen

### Abstract original

El trabajo sostiene que muchos marcos de fairness tratan raza y categorías
raciales como atributos fijos, sin considerar su carácter social, estructural,
institucional y relacional.

### Resumen en español

Es una contribución conceptual y metodológica, no un estudio de empleados ni un
benchmark predictivo. Propone revisar cómo se conceptualizan y operacionalizan
las categorías protegidas, analizar la desigualdad producida por el sistema,
reportar resultados desagregados con contexto y considerar las perspectivas de
las personas afectadas. La recomendación es especialmente relevante para no
confundir una etiqueta administrativa con una verdad semántica estable.

## Pregunta y datos

- Pregunta: ¿cómo deben tratarse las categorías raciales y la medición de grupos en la investigación de fairness algorítmica?
- Población: literatura conceptual, ejemplos históricos y marcos de fairness; no hay muestra primaria de empleados
- Tamaño: artículo de 12 páginas, sin dataset propio
- Grain: concepto, categoría y sistema sociotécnico
- Target y horizonte: fairness y desigualdad; no turnover ni horizonte predictivo
- Censura o competing risks: no aplica

## Método y validación

- Método: revisión crítica interdisciplinaria de trabajos de fairness, historia de clasificación social, encuestas, salud pública y teoría crítica
- Variables: operacionalización de raza, dimensiones de medición, categorías de grupo, análisis desagregado y contexto institucional
- Split temporal: no aplica
- Métricas: no propone un benchmark cuantitativo único ni valida un modelo
- Resultados: recomienda considerar la multidimensionalidad de las categorías, transparentar definiciones y motivaciones, analizar procesos sociales que producen desigualdad y centrar las perspectivas de grupos afectados

## Limitaciones

- Leakage: no aplica
- Sesgos: el foco está en raza y no en una implementación empresarial concreta; es una argumentación conceptual
- Generalización: no aporta evidencia de desempeño ni una receta directa para HRDA o attrition
- Fairness/privacidad: advierte que clasificar no es neutral y que las categorías pueden afectar a las personas si se usan para asignar consecuencias

## Aplicabilidad a Attrition

- Relación con Critical Tech: respalda que `gender` y otras categorías protegidas se usen sólo para auditoría autorizada, con definición, procedencia y finalidad documentadas
- Variables disponibles relacionadas: campos protegidos para fairness audit; no deben entrar al targeting del modelo sin una decisión de gobierno explícita
- Qué adoptar: documentar quién define la categoría, qué mide, qué población cubre y qué decisión habilita; reportar desagregación sin exponer celdas pequeñas
- Qué probar como challenger: no aplica como feature predictiva
- Qué posponer: inferir categorías protegidas, crear proxies o convertir resultados de auditoría en acciones individuales

## Acción y decisión

- Señal asociada: diferencia de desempeño o cobertura entre grupos, interpretada dentro del contexto de medición
- Palanca potencial: definición semántica, auditoría, revisión humana y participación de stakeholders
- Acción candidata: usar el paper para diseñar la puerta de fairness y la revisión de categorías antes de reportar resultados
- Métrica de seguimiento: métricas de fairness seleccionadas explícitamente, más cobertura, estabilidad y revisión cualitativa; no una única métrica universal
- Decisión: `referencia conceptual` y `gobierno adoptado`

## Trazabilidad

- Evidencia consultada: OpenAlex work `W2992319600`; ACM DOI; arXiv `1912.03593`
- Sección/página si el texto completo fue revisado: Abstract, Introduction, secciones 5.2–5.5 y Conclusion; PDF arXiv de 12 páginas
- Limitaciones de acceso: texto abierto consultado; no se conservó una copia local

