# C + QVoice: cierre de comparación y solapamiento

Fecha: 9-oct-2026. Modo: `presentation`. Alcance: experimento predictivo y
diagnóstico de una representación derivada; no es un nuevo assessment de las
43 variables y no modifica scores ni artefactos anteriores.

## Preguntas y decisiones previas al cálculo

1. ¿La extensión C + Q archivada satisface el criterio establecido frente a C?
2. ¿El promedio de preguntas que también tienen coeficiente propio introduce
   redundancia, y mejora al retirarla?

Población: Engineering, Employee, Regular, activo, sin RF360 por snapshot.
Grano: persona-mes exclusivamente en RAM según autorización del 1-oct-2026.
Objetivo: salida voluntaria en seis meses; prioridad del 30% y sensibilidades
del 20% y 40%. El 30% es un escenario analítico, no un presupuesto confirmado.
Conocimiento máximo: 7-sep-2026. Encuesta 2024 para 2025 y encuesta 2025 para
2026, con continuidad del episodio. No se introduce la encuesta 2026.

Se conservan las ventanas externas agosto–diciembre 2025 y enero–febrero 2026.
Las ventanas se conocen de trabajos previos: esta revisión no añade un holdout
virgen. No se transforma una colección de meses solapados en periodos
independientes ni se cambia la regla para conseguir una victoria.

## Evidencia previa que orienta la prueba

Los C + Q seleccionados en ambos periodos externos no contienen `qv_mean33`.
El artefacto final de septiembre sí lo contiene. Primero se reproducen los
modelos externos exactos; la presencia de media en el modelo final no explica
retroactivamente su desempeño. Las referencias previas sirven como contratos
a reconciliar, no como nuevas mediciones.

## Variable actual: promedio sin preguntas duplicadas

- Tipo semántico: `derived_feature`, componentes `survey`.
- Concepto: proporción de respuestas favorables entre los ítems comparables
  que no tienen un término individual en el candidato evaluado.
- Numerador: suma de indicadores favorables de los ítems restantes.
- Denominador: número fijo de esos ítems, con igual peso.
- Exclusión: mapping por texto canónico exacto del diccionario congelado;
  nunca por un número de pregunta supuesto. Career puede no formar parte de
  los 33 ítems; en ese caso no se elimina ningún ítem por ese término.
- Missing: se exige que estén válidos los 33 ítems originales. Así el cambio
  de representación no cambia elegibilidad. Se conservan los estados de no
  respuesta y cambio de episodio; no se imputan como respuestas negativas.
- Bandas: `<50`, `50–69`, `70–79`, `80–89`, `90–99`, `100`, mediante
  comparaciones enteras exactas. La variable no es una media de respuestas
  Likert; es una proporción de indicadores favorables llevada a bandas.
- Aceptación: mapping estable entre waves, cero discrepancias de bandas entre
  cálculo vectorizado e implementación escalar independiente, cero diferencias
  en elegibilidad frente al promedio original y cero cambios en los modelos
  congelados. Fórmula, estados y componentes se guardan antes del ajuste.

## Comparación acotada de representaciones

Por cada origen, reutilizar la búsqueda interna archivada para identificar el
mejor candidato que incluye media y al menos otro término. Esa elección sólo
usa el pasado de dicho origen. Mantener sus otros términos para comparar:

1. `overlap`: preguntas individuales + media original de 33.
2. `disjoint`: mismas preguntas + media de ítems restantes.
3. `items_only`: mismas preguntas individuales, sin media.

Para cada representación elegir L2 en {0.1, 1, 10} en los mismos dos intervalos
internos del experimento. Reajustar sólo la corrección Q antes de evaluar la
ventana externa. C permanece congelado. La selección ampliada puede conservar
el C + Q original si obtiene menor Brier interno. No elegir representación
según los resultados externos. No repetir los 780 ajustes por origen.

La prueba es condicional al mejor subconjunto original que contenía media;
no agota todos los subconjuntos posibles de las nuevas representaciones.
El corte final septiembre se analiza y archiva aparte, sin presentarlo como
modelo ya evaluado después de su ajuste.

## Métricas y criterio

Reproducir probabilidades y métricas agregadas de C/CQ archivados. Comparar
captura, log-loss, Brier, PR-AUC, sesgo, error por grupo, error grupo-mes y
peor error publicable. Agrupación principal común: antigüedad × salidas de
equipo × nivel. Sensibilidad separada: añadir adquisición registrada; no
confundir mejor granularidad con mejor estimador.

Conservar la regla original de CQ: captura superior en ambos periodos,
IC95 pareado positivo, error por grupo/grupo-mes no mayor a C + 0.1 pp,
pérdidas no peores que C en más del 0.5% relativo, y aporte frente al control
de disponibilidad. Bootstrap de personas, 500 réplicas, iguales pesos por
periodo. Intervalos condicionales; no corrigen múltiples comparaciones.

El veredicto distinguirá: mejora media observada, cumplimiento de la regla de
sustitución y diagnóstico del promedio. Si no se cumple, se cierra el
experimento con C como referencia y un criterio explícito para reconsiderarlo.

## Diagnóstico de colinealidad

Medir correlaciones de respuestas y media, rango de la matriz de indicadores,
número de condición y VIF cuando la matriz sea invertible. Separar:

- todas las filas, donde los indicadores de no respuesta pueden repetirse;
- casos completos, con referencias reaprendidas para el diagnóstico;
- observaciones únicas persona-wave para evitar contar la misma encuesta
  reiteradamente en la correlación descriptiva.

Umbrales descriptivos: |r| >= 0.8, VIF >= 10 y número de condición >= 30
indican revisión; no son reglas de promoción ni prueba causal. Un VIF de una
matriz singular se declara no identificable, no se sustituye por una
pseudoinversa fingiendo finitud. L2 estabiliza el ajuste pero no hace únicos
los efectos sin penalizar.

## Evidencia y entrega

Consulta temporal guardada: copia exacta de
`queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql` bajo
un nombre nuevo. Cliente read-only del skill `attrition-redshift-db`;
reconciliación de población, etiquetas y fuentes antes de interpretar.
La autorización permite filas y llaves efímeras sólo en RAM. Se guardan
parámetros, diagnósticos agregados, métricas, informe español y manifest.
Las reglas de derivación de `evaluate-attrition-variable` se aplican al
diagnóstico sin asignar scores ni regenerar workbooks. `morgan-vis` guía el
gráfico comparativo y sus límites. Se comprobarán cálculos y reproducción
porque el usuario solicitó explícitamente validar ambos puntos.
