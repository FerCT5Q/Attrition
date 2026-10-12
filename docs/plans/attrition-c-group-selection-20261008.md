# Seleccionar agrupaciones de C conservando B con sus cortes como referencia

Plan previo al cálculo, 8-oct-2026. Modo: `presentation`.

## Pregunta y alcance

¿C identifica mejor los grupos de riesgo al usar cruces interpretables de variables,
y supera a B con antigüedad × salidas del equipo × nivel? Se conservan los
modelos hazard B y C archivados. La búsqueda cambia únicamente la representación
de sus predicciones. B+QVoice queda como artefacto de referencia conservado.

Hipótesis: los cruces de dos o tres características laborales conservan más de
la concentración de salidas de C que ocho hojas, sin perder precisión útil
dentro de los grupos prioritarios. Asociación predictiva; no causalidad.

## Datos, semántica y tiempo

- Autorización: `config/attrition_model_in_memory_training_authorization_20261001.json`.
- Población: Engineering, Employee, Regular, activo, sin RF360.
- Consulta existente: `queries/profiles/engineering_model_c_person_month_20261008.sql`.
- Grain: persona-snapshot en RAM; resultados exclusivamente agregados.
- Predicción: salida voluntaria en seis meses; calendario avanza y otras
  características permanecen como en el snapshot. No se recalibra el hazard.
- Periodos externos: febrero–julio 2024, agosto 2024–enero 2025,
  febrero–julio 2025 y agosto 2025–enero 2026.
- Antes de cada origen se eligen cortes usando las seis últimas fotos cuyo
  seguimiento R6 terminó antes de ese origen. No se usan las salidas del
  periodo externo para seleccionar sus cortes.
- Es desarrollo de agrupaciones: esos resultados maduros participaron en el
  ajuste del hazard archivado. No es una validación independiente del hazard.
- Foto adicional: 22-feb-2026, seguimiento hasta 22-ago-2026, con modelos y
  selección de agosto de 2025. Se informa por separado.

## Candidatos y regla congelada

Cruzar todas las combinaciones de dos y tres dimensiones entre las siete
originales de B y las adicionales presentes en el C de cada corte temporal.
Las siete originales mantienen exactamente `coarse_keys` del script histórico.
Las adicionales usan las bandas preparadas del modelo C. Se excluyen calendario,
interacciones como dimensiones y dimensiones constantes en desarrollo.
No se evalúan disponibilidad ni scores de variables nuevos.

Árboles de hasta ocho y dieciséis hojas, profundidad tres y cuatro, mínimo
300 personas en entrenamiento. Se ajustan sólo a predicciones, en la última
foto de entrenamiento del hazard. El árbol de ocho hojas archivado se reutiliza.

Selección principal: captura al 30%; cruces dentro del 2% relativo del máximo;
entre ellos error grupo-snapshot a no más de 0.1 pp del mínimo; después menos
dimensiones, menos grupos, mayor captura y nombre estable. Un árbol sólo
sustituye al cruce si mejora captura más de 2% relativo y no empeora su error
grupo-snapshot más de 0.1 pp. La configuración ejecutable conserva los umbrales.
Selección secundaria por eficiencia Gini con parsimonia, para acercarse al
criterio histórico de B; se etiqueta como diagnóstico.

## Política común y métricas

En cada snapshot, ordenar los grupos por su riesgo predicho medio vigente.
Elegibilidad: mínimo estricto de 300 personas en esa foto. Los demás quedan
fuera de la prioridad. El límite de capacidad asigna la misma fracción a todos
los integrantes del grupo empatado: es una comparación estandarizada,
equivalente a selección aleatoria dentro del grupo, no una lista individual.
Se muestran además captura, cobertura y error al incluir o excluir grupos
completos en el límite. Capacidades: 20%, 30% y 40%; escenario principal 30%.

Comparar B cortes, C mismos cortes, B árbol 8, B árbol 16, C árbol 8,
C árbol 16, C selección principal y C selección Gini. El ordenamiento común
por riesgo vigente difiere de la comparación previa con hojas congeladas.
Los B reconstruidos sobre el frame temporal corregido no son reproducción
exacta de las cifras históricas del deck; sí de la receta hazard y de sus cortes.

Reportar captura, lift, observado/estimado, sesgo, error absoluto por grupo y
grupo-snapshot, peor grupo publicable, número de grupos/resto, variación temporal
y eficiencia Gini contra ranking individual del mismo modelo. Para Gini el
resto forma un bloque final; nunca recibe prioridad. Promediar periodos con
igual peso. Bootstrap pareado por persona, conservando ventanas juntas, con
500 réplicas; inferencia condicional a modelos, selección y política ya fijados.

Preferencia retrospectiva: captura media mayor, ganar al menos tres periodos,
IC95 positivo y no empeorar más de 0.1 pp los dos errores de grupos. No representa
promoción automática. Los años fueron explorados antes y sólo hay cuatro periodos.

## Conservación, eficiencia y comprobaciones

Restaurar cuatro B y cuatro C: cero ajustes hazard. Precálculo de categorías,
agregados con códigos y `bincount`, predicciones reutilizadas por periodo.
Hashes de artefactos anteriores antes/después; copia de código/config/SQL al
run nuevo. Reconciliar población y métricas globales con el run archivado;
comprobar seguimiento maduro, cobertura de reglas, capacidad, identidades
captura/cobertura/lift y cálculo directo por persona contra agregación. Estas
son comprobaciones del análisis, sin añadir ni ejecutar suites de software.

No persistir filas, llaves, puntuaciones individuales ni salarios exactos.
Tasas por grupo sólo con al menos 30 personas por foto seleccionada y 30
personas distintas con evento. Informe español y gráfico con fuente, población,
ventana y máximo un decimal en cifras visibles.
