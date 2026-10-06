# Plan de continuidad — salidas secuenciales de equipo

**Estado:** en curso; no publicar ni sustituir las láminas 8–9 hasta que la
evidencia agregada pase las validaciones de calendario, atribución, censura y
privacidad.

## Objetivo

Reemplazar la gráfica ambigua de **“More than 1 employee leaves”** por una
comparación descriptiva que responda:

> Después de una salida Voluntary inicial, ¿las personas que permanecen en ese
> equipo presentan una incidencia acumulada de salida distinta frente a equipos
> comparables sin una salida reciente?

El deck documenta distribución y evidencia de variables candidatas; no predice
renuncias individuales. El modelo futuro se orienta a cohortes con mayor riesgo
relativo de salida voluntaria a seis meses, para apoyar acciones de retención
aprobadas.

## Decisiones ya acordadas

| Elemento | Regla |
| --- | --- |
| Entregable | `presentation`: sólo agregados, sin IDs, nombres, managers ni atributos protegidos; `n >= 30`. |
| Población | `worker_type='Employee'`, `employee_type='Regular'`, `active_status=1` y manager no nulo al snapshot índice. |
| Evento índice | Terminación con `term_type='Voluntary'`, una sola en el equipo durante los seis intervalos cerrados `(t-6, t]` y ocurrida en el intervalo que termina en `t`. |
| Roster | Personas activas bajo el manager índice en `t`; se siguen sólo mientras continúen con ese manager. |
| Outcome | Primera salida `Voluntary` del roster en los seis cierres posteriores, atribuida al manager índice en el momento del evento. |
| Censura | Primer cambio de manager observado, salida no voluntaria o pérdida de observación. |
| Comparador | Equipos sin salida `Voluntary` en `(t-6, t]`, en el mismo snapshot y banda de tamaño `1–5`, `6–10`, `11–20` o `21+`. |
| Estimando | Incidencia acumulada a seis meses: `1 − supervivencia Kaplan–Meier`; referencia estandarizada por `snapshot × banda de tamaño` de la cohorte expuesta. |
| Láminas | Lámina 8: todos los equipos elegibles. Lámina 9: sensibilidad para equipos de 6+ reportes. |
| Interpretación | Asociación descriptiva. Prohibido afirmar causalidad, “contagio” demostrado, ranking de managers o predicción individual. |

## Artefactos ya creados

- Planes analíticos congelados:
  - `config/team_post_exit_attrition_event_study_plan_v1_20260910.yaml`
  - `config/team_post_exit_attrition_event_study_plan_v2_20260910.yaml`
  - `config/team_post_exit_attrition_event_study_plan_v3_20260910.yaml`
- Solicitud de preflight:
  - `config/team_post_exit_attrition_event_study_run_request_20260910.yaml`
- Preflight de portafolio completado:
  - `output/assessments/team-post-exit-attrition-preflight-20260910-r2/`
- Consultas en desarrollo:
  - `queries/audits/team_post_exit_attrition_event_study_20260910.sql`
  - `queries/audits/team_post_exit_attrition_interval_20260910.sql`

La dependencia `Team turnover` se agregó al preflight sólo porque el catálogo
la declara como dependencia de **More than 1 employee leaves in a year**. No se
debe revaluar ni modificar su evidencia dentro de este trabajo.

## Bloqueo actual

La primera consulta integral expandía roster de controles × seis periodos de
seguimiento. Redshift cerró la conexión por carga antes de devolver resultados.
La variante de un solo intervalo también fue demasiado costosa al reconstruir
historia y roster en la misma consulta. No hay evidencia ejecutada ni métricas
publicables de esta hipótesis todavía.

No usar la gráfica anterior como sustituto ni inventar una curva mientras este
bloqueo persista.

## Ruta segura para retomarlo

1. Confirmar que no quede una ejecución pesada de Python/Redshift activa antes
   de volver a consultar.
2. Mantener `presentation` y usar obligatoriamente los skills
   `attrition-redshift-db` y `evaluate-attrition-variable` para cualquier nueva
   consulta o cambio de definición.
3. Dividir la reconstrucción en consultas agregadas más pequeñas y guardadas:

   - Auditoría A: calendario mensual, duplicados y conflictos de
     `employee_id × snapshot × manager` en el periodo de análisis.
   - Auditoría B: eventos de terminación deduplicados por `employee_id × term_date`,
     dominio de `term_type` y atribución al último manager histórico válido.
   - Auditoría C: conteos agregados de episodios índice y controles por
     `snapshot × banda de tamaño`, con supresión si el control no alcanza 30.
   - Auditoría D: seis consultas de hazard por intervalo, que devuelvan sólo
     `scope × grupo × mes de seguimiento` ya estandarizado; no devolver estratos
     pequeños ni IDs.

4. Antes de acumular los hazards, verificar por cada mes y alcance:

   - dos grupos disponibles: expuesto y referencia ajustada;
   - `n` agregado en riesgo >= 30;
   - hazard entre 0 y 100;
   - eventos no mayores al número en riesgo;
   - controles sin salida Voluntary en la ventana anterior;
   - ningún outcome anterior o igual al snapshot índice.

5. Sólo si los seis puntos pasan, generar JSON congelado bajo
   `output/distribution/` con:

   - hashes de SQL y resultados;
   - fecha de ejecución, población, periodo y grain;
   - hazards e incidencia acumulada por alcance y grupo;
   - conteos agregados de riesgo, eventos, censura y estratos suprimidos;
   - resultado `pass` o `blocked` y limitaciones.

6. Crear o ajustar el builder de evidencia para ejecutar las consultas de forma
   secuencial, con timeout controlado. No guardar resultados intermedios de
   cohortes menores de 30.
7. Actualizar `tools/build_distribution_html_v2.py` únicamente tras contar con
   JSON `pass`:

   - reemplazar las láminas 8 y 9 por líneas Plotly;
   - títulos propuestos: “¿Una salida inicial precede más salidas?” y
     “Sensibilidad: equipos de 6+ personas”;
   - incluir nota visible: “Asociación descriptiva; no demuestra causalidad ni
     contagio.”;
   - re-renderizar Plotly en los cuatro temas;
   - preservar las otras 43 láminas, navegación y manifest.

8. Validar al final:

   - 45 láminas, nav y manifest intactos;
   - sólo cambiaron las láminas 8–9 y sus labels de navegación aprobados;
   - curvas y notas sin clipping en los cuatro temas;
   - README de la variable actualizado con método, consulta, resultados,
     limitaciones y diferencia entre evidencia retrospectiva y feature
     time-safe.

## Criterio de salida

El trabajo termina en uno de dos estados explícitos:

1. **`pass`:** evidencia agregada reproducible, con curvas publicables y las
   dos láminas sustituidas.
2. **`blocked`:** Redshift o la calidad de datos impiden demostrar una curva
   publicable; se conserva la documentación del intento y se sustituye el
   contenido por una nota de limitación, no por una afirmación sin evidencia.
