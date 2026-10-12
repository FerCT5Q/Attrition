# C + QVoice: revisión de solapamiento y cierre retrospectivo

Fecha: 9-oct-2026. Modo `presentation`.

## Decisión

La revisión retrospectiva está terminada. **C + Q mejora en promedio, pero
no cumple la regla conjunta para sustituir C**: gana en captura en
agosto–diciembre 2025 y empata en enero–febrero 2026. No hay nueva evidencia
prospectiva. Se mantiene C como referencia.

| Métrica | C | C + Q archivado |
|---|---:|---:|
| Captura al priorizar 30% | 42.4% | 43.1% |
| Log-loss R6 × 1000 | 138.8 | 137.7 |
| PR-AUC | 4.9% | 5.5% |
| Error grupo-mes | 1 pp | 1 pp |

El error grupo-mes baja ligeramente antes de redondear. La mejora media de
captura es 0.7 pp; IC95 recalculado [0.1, 1.2] pp con 500 réplicas de personas.
Cumple siete de ocho condiciones. La falta de una segunda victoria impide
promoverlo bajo la regla original; no equivale a ausencia de aporte QVoice.
Los periodos y su seguimiento se superponen parcialmente. Las medias tienen
igual peso por periodo; no son salidas únicas de una sola cohorte.

## Qué se confirmó del promedio

1. Los CQ históricos evaluados no habían seleccionado `qv_mean33`. Sus
   mejoras frente a C no provienen de usar promedio más preguntas.
2. Se compararon tres representaciones sobre el mejor subconjunto con media
   seleccionado en el pasado de cada origen: media de 33 más preguntas,
   media excluyendo preguntas individuales y sólo preguntas. L2 se eligió
   con los mismos intervalos internos; el periodo externo no eligió la
   representación. Son pruebas condicionadas al subconjunto original, no
   una nueva búsqueda exhaustiva.
3. La media sin duplicación y la media completa capturan lo mismo: 42.8% en
   promedio al 30%. Las diferencias de pérdidas son pequeñas y sus intervalos
   incluyen cero. La variante sin promedio captura 43.1%.
4. La selección interna ampliada conserva el CQ original en ambos periodos.
5. En el corte final, la media sin duplicación contiene 28 ítems, excluyendo
   Q8, Q10, Q11, Q13 y Q17. Career no pertenece a los 33 ítems comparables.
   La selección interna la favorece por menos de 0.1% relativo en Brier;
   se guarda como una variante experimental sin evaluación posterior.

## Colinealidad medida

En los casos completos del modelo final CQ, el VIF máximo pasa de 4.1 a 3.5
y el número de condición de 5.3 a 5 al retirar las preguntas del promedio.
No se observa colinealidad severa según los umbrales descriptivos
preestablecidos de VIF 10 y condición 30.

La matriz indicadora completa tiene rango 20 para 32 columnas variables:
los estados de no respuesta/cambio de episodio crean redundancias exactas
compartidas entre preguntas. En casos completos, las 11 columnas tienen rango
11. L2 permite ajustar el modelo, pero los efectos separados de indicadores
redundantes no son identificables sin la penalización. Quitar preguntas de la
media no elimina esas redundancias de ausencia.

El diagnóstico complementario de las variables BQ usa la misma muestra de
C, no reproduce la ventana original de ajuste BQ. Se declara esa diferencia
en el informe. Las correlaciones descriptivas usan personas-wave únicas.

## Artefactos y trazabilidad

- Carpeta nueva: `output/analysis/engineering/20261009/c-qvoice-overlap-v1/`.
- [Informe](../../output/analysis/engineering/20261009/c-qvoice-overlap-v1/informe.md).
- `results.json`, `verdict.json`, `verification.json`, `manifest.json`.
- Variante final: `trained-model/selected-model.json` y `trained-model/disjoint/model.json`.
- Consulta: `queries/profiles/engineering_c_qvoice_overlap_person_month_20261009.sql`,
  copia exacta de la consulta CQ, ejecutada el 9-oct-2026 con corte 7-sep-2026.
- Población: Engineering, Employee, Regular, activo, sin RF360.
- 36 ajustes de correcciones, cero reajustes de C; 8.3 minutos de cálculo.
- Se reprodujeron métricas y población; 907 comprobaciones pasaron y
  416 archivos anteriores conservaron sus hashes. No se guardan filas,
  respuestas, llaves ni predicciones individuales. No cambian scores.

La evidencia nueva cierra el diagnóstico del solapamiento. Para confirmar una
mejora posterior al corte final se necesitan fotos futuras con seis meses de
seguimiento, manteniendo los parámetros y criterios congelados. No se
presentan reanálisis de periodos conocidos como esa validación nueva.
