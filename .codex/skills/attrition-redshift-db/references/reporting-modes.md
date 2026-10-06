# Modos de entrega para resultados agregados

Decide y registra el modo antes de ejecutar una consulta o generar un reporte.
Si el destinatario no se declara de forma inequívoca, usa `presentation`.

| Modo | Cuándo se usa | Etiquetas de categorías protegidas | Controles no negociables |
| --- | --- | --- | --- |
| `internal_analysis` | El solicitante dice expresamente que el reporte es interno o exploratorio para su análisis. | Se pueden mostrar los valores realmente almacenados, por ejemplo en `gender`, con sus conteos y porcentajes agregados. | Cada bucket visible tiene `n >= 30`; marcar el artefacto como análisis interno; no reutilizarlo como presentación. |
| `presentation` | Presentaciones, reportes compartibles, entregables para liderazgo o destino incierto. Es el valor por defecto. | Suprimir o anonimizar las etiquetas protegidas. | Mantener cohortes de `n >= 30` y las restricciones generales. |

En ambos modos está prohibido devolver filas de empleados, identificadores,
nombres, correos, identidad de managers, domicilios, fechas de nacimiento,
texto libre o valores individuales. La compensación exacta tampoco se muestra:
para exploración interna se usan bandas, percentiles, medias o medianas
agregadas.

Para una consulta de `internal_analysis` que devuelva una etiqueta protegida,
usar `COUNT(DISTINCT employee_id)` por bucket y filtrar con `HAVING` para que
cada grupo cumpla el umbral. El resultado debe indicar población, fecha o
ventana, grain, denominador y el modo de entrega.
