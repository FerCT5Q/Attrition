# Random Survival Forest: plan previo

Fecha: 8-oct-2026. Modo `presentation`. Objetivo: completar la familia pendiente
de la presentación y compararla con B, C y sus variantes para identificar grupos
prioritarios con buenas estimaciones e interpretación accesible.

## Población, tiempo y outcome

Se reutilizan las representaciones y la población de C: Engineering, Employee,
Regular, activo en la foto mensual, sin RF360. Cada foto es un origen de predicción
con sus covariables conocidas; las personas pueden contribuir a varias fotos.
La unidad de remuestreo de incertidumbre es la persona, conservando sus ventanas.

El outcome es la misma salida voluntaria dentro de seis meses de B/C. La consulta
de C se amplía con la distancia en días a la primera salida voluntaria de esa
ventana y los indicadores de episodio ya usados para QVoice. Esas columnas y
las llaves efímeras permanecen sólo en RAM. Se conserva el SQL de origen y se
comprueba la igualdad de población, etiquetas y métricas de referencia.

Para el bosque, el tiempo se discretiza en seis meses calendario desde cada
foto. Evento en mes j si ocurre después del límite j-1 y hasta el límite j.
En cada origen de ajuste sólo se usan meses completos terminados antes del
corte; las ventanas incompletas se censuran en el último mes completo. Se
omiten ventanas sin un mes completo. Se exige duración entre 1 y 6, evento
dentro del seguimiento disponible y coincidencia exacta con y_6m al madurar.
El bosque produce S(1),...,S(6); R6 = 1-S(6). No es un clasificador de sí/no.

Las otras salidas conservan la convención de B/C: no son el evento voluntario
objetivo. No se introduce censura adicional por esas salidas ni un modelo de
riesgos competitivos. Se heredan los límites sobre registro tardío y observación
de eventos de la fuente; la validación no convierte el registro retrospectivo
en un historial de revisiones de base de datos.

## Selección y calibración

Se probarán ocho configuraciones: señales base B o todos los conceptos candidatos
de C, hojas mínimas de 150/400 y fracción de variables sqrt/0.5. Las interacciones
explícitas se omiten: el bosque aprende divisiones e interacciones. Codificación
one-hot ajustada sólo con el entrenamiento; faltantes como categorías explícitas.
Se usan 80 árboles en selección, 200 al ajustar la versión de cada origen,
profundidad máxima 12, muestra bootstrap de hasta 40000 filas por árbol y cuatro
hilos. La biblioteca es scikit-survival, aislada en tools/.deps/rsf.

Antes de cada origen externo se reservan las seis últimas fotos cuyo R6 terminó
antes del corte. El bosque auxiliar se ajusta antes de la primera foto reservada.
Las primeras tres eligen hiperparámetros: captura al 30% en los cortes comunes,
tolerancia relativa 2%; después menor log-loss, error grupo-mes y simplicidad.
Las últimas tres ajustan un único multiplicador del riesgo acumulado mediante
log-loss. R calibrado = 1-(1-R crudo)^exp(a); conserva el orden individual.
La calibración usa predicciones ajenas al ajuste auxiliar. Al reajustar el bosque
con la historia disponible al origen se transfiere ese multiplicador, por lo
que se evaluarán por separado la versión cruda y calibrada. No se elige una de
ellas mirando el periodo externo. La versión calibrada es el candidato principal.

## Comparaciones

- Cuatro periodos de seis fotos: febrero–julio 2024, agosto 2024–enero 2025,
  febrero–julio 2025 y agosto 2025–enero 2026. Foto madura adicional: febrero 2026.
- Bloque comparable con QVoice: agosto–diciembre 2025 y enero–febrero 2026.
  Restaurar sus modelos históricos; no aplicar el modelo final retrospectivamente.
- B/C con sus cortes comunes; árboles archivados como variantes; C con las
  selecciones históricas de cuatro variables. RSF con cortes comunes y un árbol
  explicativo de hasta 16 hojas, ajustado a sus predicciones en la última foto
  de entrenamiento. Las hojas explican el bosque, no lo sustituyen.
- Capacidades 20%, 30% principal y 40%; mínimo 300 personas por grupo/foto.
  Los grupos insuficientes van a resto y no se priorizan. Tasas observadas
  publicables con al menos 30 personas por foto y 30 personas distintas con evento.
- Métricas globales: log-loss, Brier, PR-AUC, sesgo y error de estimación;
  por prioridad: captura, lift, error por grupo y por grupo-mes. Comparar
  también las estimaciones sobre la misma prioridad de C.
- Regla frente a C: IC95 de mejora de captura positivo, al menos tres de cuatro
  victorias, errores por grupo/grupo-mes como máximo +0.1 pp y deterioro relativo
  de log-loss/Brier como máximo 0.5%. No se sustituye automáticamente ningún modelo.
  Bootstrap pareado por persona, 500 réplicas; intervalos condicionales a ajustes
  y selecciones, sin corrección por comparaciones múltiples.

## Artefactos y límites

Carpeta nueva random-survival-forest-v1. Guardar configuración, fuentes congeladas,
modelos de inferencia sin filas/llaves/muestras bootstrap, resultados agregados,
selecciones, calibradores, grupos, informe y hashes de preservación. Los modelos
anteriores no se reajustan. El modelo final RSF se ajusta al corte 7-sep-2026 y
se distingue de los modelos históricos que sustentan las métricas.

La selección previa de B/C y el uso repetido de estos periodos hacen retrospectiva
la comparación. Mayor captura no demuestra eficacia causal de una intervención.
Las importancias y reglas del bosque se describen como señales predictivas.
