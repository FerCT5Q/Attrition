# Anexo reproducible

Modo `presentation`. SQL principal: `queries/profiles/engineering_bu_l3_person_month_20261012.sql`; metadata y join BU en `input-evidence/bu-l3-*.json`; eventos únicos en `input-evidence/unique-events.json`. Consulta read-only con la autorización de persona-mes sólo en RAM de 1-oct-2026.

El manifiesto conserva fechas, configuración, hashes y tiempos. La carpeta `source/` congela ejecutables y especificaciones. Los modelos históricos CQ se restauran; FQ y FQ + BU se ajustan conservando variables y L2. No se ejecuta otra búsqueda de variables.

| Periodo | Métrica | Archivado | Reproducido | Diferencia | Tolerancia 1e-8 |
|---|---|---|---|---|---|
| aug_dec_2025 | log_loss | 0.1 | 0.1 | 0 | Sí |
| aug_dec_2025 | brier | <0.1 | <0.1 | <0.1 | Sí |
| aug_dec_2025 | capture_percent | 43.5 | 43.5 | 0 | Sí |
| aug_dec_2025 | group_snapshot_mae_pp | 1 | 1 | >−0.1 | Sí |
| jan_feb_2026 | log_loss | 0.1 | 0.1 | <0.1 | Sí |
| jan_feb_2026 | brier | <0.1 | <0.1 | 0 | Sí |
| jan_feb_2026 | capture_percent | 42.8 | 42.8 | 0 | Sí |
| jan_feb_2026 | group_snapshot_mae_pp | 0.9 | 0.9 | <0.1 | Sí |

El `results.json` conserva precisión numérica para auditar estas diferencias; el texto usa como máximo un decimal. La covarianza se calcula mediante ecuaciones apiladas: bloque RH, bloque QVoice y derivada cruzada del offset. La matriz meat suma scores centrados por persona; bread incluye curvatura observada y penalización. Se usa pseudoinversa con tolerancia declarada y se guarda rango/eigenvalor mínimo.

El gradiente del riesgo conserva el avance de calendario de los seis hazards y el recorte de cada predictor lineal. La validación sintética compara derivadas con diferencias finitas y comprueba la invariancia del sandwich al duplicar filas y penalización dentro de la misma persona.

Bootstrap: multinomial exacto de personas, semilla 20261012, 500 réplicas compartidas. Las métricas se recalculan por réplica y después se promedian los dos periodos con peso 1/2. Intervalos percentiles 2.5%/97.5%, condicionados a modelos y prioridades fijas. No se guarda la matriz de pesos ni filas.

La subdivisión considera un grupo base válido con al menos 300 personas por foto. Los mínimos hijos 100/150/200 se aplican a las categorías de BU reales; `(unknown)` y `(other)` se agrupan en remanente. Exige al menos dos hijos identificables; un remanente positivo por debajo del mínimo hace conservar el padre. REST se determina sólo por invalidez del padre base, y por eso su población se conserva exactamente.

Reproducción de cálculo en una carpeta nueva: copie la configuración con otro `run_id` y `output`, prepare allí la entrega documental, ejecute el cálculo y después el render sobre esa salida. `--resume-models` recupera modelos guardados tras una interrupción, pero exige volver a cargar datos en RAM porque no existen cachés individuales.

Pruebas: `.venv/Scripts/python.exe -B -m unittest discover -s tests -p test_julia_review_statistics.py -v`. Render: `.venv/Scripts/python.exe -B tools/render_julia_rh_review.py`. No hay cambios en reglas o contratos de los skills; esta ejecución no es un assessment y no asigna scores.

La lectura principal ajustó cuatro bases RH y cuatro correcciones QVoice, además de nueve bases y nueve correcciones auxiliares para el escalar (tres orígenes de enero por modelo). CQ principal se restauró. El suplemento hizo una lectura adicional enfocada de las fechas de evaluación y QVoice, sin ajustes, porque los primeros agregados no conservaban captura/error por estado y observado publicable en fichas. Esto se aparta del objetivo de una sola carga compartida, conservando el máximo de ajustes principales. SQL y seis reconciliaciones exactas están en `cohort-diagnostics-supplement.json`.

Salidas únicas por ficha: `queries/audits/julia_review_unique_group_events_20261012.sql`, agregado persona-fecha con los mismos cortes; se reconcilian personas y exposiciones con evento contra RAM antes de publicar. Una salida puede aparecer en varias fotos de seis meses: no se suman las fichas para obtener salidas únicas de toda la ventana. Los márgenes de conteos de ventana se suprimen cuando permitirían reconstruir una foto de menos de 30 personas.

Pendientes que limitan uso por RH: acreditar publicación histórica de IOS y fecha real de publicación QVoice; confirmar responsables funcionales y capacidad con RH; validar prospectivamente una cohorte nueva. La supresión es por particiones publicadas; no equivale a una garantía formal de anonimización frente a otras bases externas.
