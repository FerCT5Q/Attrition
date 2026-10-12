# Variable adicional en la agrupación de C

Fecha de documentación: 8-oct-2026. Modo `presentation`.

## Variable y significado

La variable adicional es **adquisición registrada (`acquisition_recorded`)**.
Representa la existencia de un registro de adquisición asociado a la persona
en la fuente utilizada por C. **«Sin registro» no confirma que la persona nunca
haya venido de una adquisición.** Esta lectura conserva la interpretación
documentada en el experimento; no atribuye causalidad al attrition.

## Cruce documentado

**Antigüedad × salidas previas del equipo × nivel × adquisición registrada.**

Corresponde a la alternativa `C_plus1`, que añade un cuarto corte a la agrupación
actual de C para el escenario principal de priorizar al **30% de la población**.
`acquisition_recorded` ya forma parte de las variables del C archivado; aquí
se utiliza también para dividir los grupos. Las predicciones proceden de ese C.

La última selección tiene origen **1-ago-2025**. Aplicada a la foto del
**22-feb-2026**, con seguimiento hasta el **22-ago-2026**, produce **23 grupos
elegibles**, con al menos **300 personas por grupo y foto**. Los 23 son el total
de grupos elegibles, no el número de grupos que necesariamente se atenderían.
El número puede cambiar entre fotos mensuales.

## Motivo y alcance de la recomendación

En esa foto de febrero, al priorizar al 30%, la captura pasa de **42.7% a
42.9%**. En los cuatro periodos históricos, la política de añadir una variable
obtiene **45.7%**, frente a **45.4%** con los cortes actuales: mejora de **0.3
puntos porcentuales**, pequeña y con cumplimiento marginal de la regla.

Las medias históricas corresponden a la selección realizada en cada periodo.
Adquisición registrada fue elegida en los dos orígenes más recientes; los
anteriores eligieron otras variables. Por tanto, esa mejora media no prueba
por sí sola la superioridad del mismo cruce de adquisición en todos los periodos.

Se registra como alternativa para continuar revisando bajo capacidad del 30%.
La documentación solicitada no constituye una promoción automática de la
alternativa a agrupación definitiva.

## Evidencia archivada

- Población: Engineering, Employee, Regular, activo, sin RF360; salida
  voluntaria a seis meses.
- [Selección congelada](selected-groupings.json): origen y definición de `C_plus1`.
- [Resultados agregados](results.json): `extension.evaluation.C_plus1` para
  febrero de 2026 y `summary.30` para la comparación histórica.
- [Informe completo](informe.md): criterios de selección, incertidumbre y
  comparación con las otras agrupaciones.
- [Consulta archivada](source/queries/profiles/engineering_model_c_person_month_20261008.sql):
  ejecutada el 8-oct-2026, con conocimiento hasta el 7-sep-2026.

Esta nota documenta la evidencia existente del experimento; no incorpora
resultados de una ejecución nueva.
