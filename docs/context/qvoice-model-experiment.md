# Experimento QVoice para el modelo de Engineering

Implementación del [plan del 6 de octubre](../plans/attrition-model-qvoice-experiment-20261006.md). Los entregables se clasifican como `presentation`.

## Qué se compara

El control es el **modelo B confirmado el 3 de octubre de 2026**: diez features, hazard `cloglog`, sin tendencia ni recalibración. La configuración fija 17 variantes de QVoice, los dos periodos principales, las combinaciones, los controles de disponibilidad y la ablación de 31 preguntas sobre la cohorte completa original de 33.

La población es Employee, Regular, activa, Engineering, con RF360 excluido. La frontera inicial de conocimiento es el 7 de septiembre de 2026. El modelo procesa filas sólo en memoria, bajo `config/attrition_model_in_memory_training_authorization_20261001.json`. Los archivos de salida contienen agregados; las tasas publicadas requieren al menos 30 personas y 30 eventos.

## Fechas y versiones de preguntas

La disponibilidad predictiva requiere una **fecha documentada de publicación de resultados**. Se registra por wave en `config/qvoice_model_experiment_20261006.yaml`:

```yaml
availability:
  date: null
  status: pending
  evidence_reference: null
```

Al contar con la evidencia, se crea una nueva versión de configuración con la fecha, `status: verified` y una referencia a un documento existente. Una fecha de respuesta, lanzamiento, creación del Excel o modificación del archivo no acredita por sí sola la publicación. La validación rechaza fechas verificadas sin referencia documental.

El item Career goals de 2024 incluye “Overall”; su equivalencia con 2025–2026 queda pendiente. Q6 y Q9 no existen en la fuente binaria de 2024. Heartbeat requiere los 53 ítems ordinales y al menos 38 respuestas válidas; una wave con sólo 52 ítems no reproduce esa definición.

La auditoría de Heartbeat revisa el dominio de las 53 entradas que forman el promedio personal y recalcula de forma independiente los seis signos seleccionados. Sus 18 segmentos de 2026 se concilian con el JSON histórico usando la plantilla original y la ventana hasta el 23 de agosto. La conciliación reproduce por separado el SQL histórico sin límite de snapshot de registro de eventos y documenta las diferencias frente al corte vigente. Todas las cifras principales de Engineering conservan el corte del experimento.

Una nueva wave disponible reemplaza a la anterior aunque no exista respuesta enlazable. Las respuestas caducan a los 12 meses y no atraviesan una salida y recontratación. Los faltantes, valores inválidos, preguntas ausentes y registros sin enlace se conservan separados de la respuesta no favorable.

## Ejecución

Desde la raíz del proyecto, elegir una carpeta nueva. Los ejemplos usan `output/analysis/engineering/20261006/qvoice-experiment-v1`, que ya contiene la primera ejecución y debe conservarse.

### 1. Inventario y planes

```powershell
.venv\Scripts\python.exe -B tools/qvoice_model_preflight.py --output <run>/preflight
.venv\Scripts\python.exe -B tools/qvoice_model_assessment.py --preflight <run>/preflight
```

El primer comando lee encabezados, diccionario y metadata de HRDA. El segundo congela el preflight conjunto y los planes explícitos versionados de `config/qvoice_model_plans/`. No se calculan scores con los workbooks históricos.

### 2. Reproducción del control

```powershell
.venv\Scripts\python.exe -B tools/qvoice_model_control.py --output <run>/control
```

Comprueba los totales, los 82 parámetros y las métricas de los cuatro periodos históricos. La comparación QVoice verifica también que el control corresponda a la misma configuración, fuente y SQL.

### 3. Evidencia y assessment por concepto

```powershell
.venv\Scripts\python.exe -B tools/qvoice_model_evidence.py --run-root <run>
```

La sesión conserva temporalmente las columnas estructuradas en memoria. El orden es:

```text
intent → career → mean33 → engagement → connection → wellbeing → confidence → heartbeat
```

Para cada concepto:

1. Ejecutar `audit <id>`.
2. Revisar `variables/<id>/latest-evidence.json` y la evidencia a la que apunta: dominios, fórmulas, enlaces, cohortes, tasas y conciliaciones.
3. Si aparece una brecha material, escribir una revisión explícita del plan, congelarla mediante el preflight y repetir `audit <id>`. Cada revisión de evidencia conserva la anterior.
4. Ejecutar `finalize <id>` para crear el notebook ejecutado, HTML, Excel, JSON y documentación acumulada.
5. Revisar el resultado antes de iniciar el concepto siguiente.

La sesión impide avanzar a otro concepto sin finalizar el actual. `quit` libera las respuestas de memoria. Los assessments se publican en `output/assessments/`; `assessment-reference.json` conserva su ubicación y hash.

En un entorno que bloquee el kernel de Jupyter, se prepara el comando del assessment usando sólo los agregados ya guardados:

```powershell
.venv\Scripts\python.exe -B tools/qvoice_model_assessment.py --preflight <run>/preflight --run-root <run> --prepare-candidate <id>
```

El archivo `assessment-command.json` contiene los argumentos exactos y los hashes de entrada. Se ejecuta mediante el mecanismo autorizado del entorno y después se registra con `finalize <id>` en la sesión. `--register-candidate <id>` permite registrar una regeneración de un reporte anterior cuando ya existe un manifest validado con los mismos inputs. Una carpeta `.working` fallida no es un assessment publicado.

### 4. Comparación y entregables

```powershell
.venv\Scripts\python.exe -B tools/verify_qvoice_model_sql.py --output <run>/validation/model-sql-check.json
.venv\Scripts\python.exe -B tools/qvoice_model_experiment.py --run-root <run>
.venv\Scripts\python.exe -B tools/build_qvoice_model_report.py --run-root <run>
```

La verificación SQL usa `EXPLAIN` y una sonda con `LIMIT 0`; no devuelve filas de empleados. Si faltan fechas verificadas, el comparador registra **evidencia temporal insuficiente** y no entrena modelos con fechas supuestas. El informe, los gráficos y el Excel consolidado se construyen desde los ocho assessments terminados.

Para una configuración distinta, todos los comandos aceptan `--config <archivo>`. Se necesita un preflight y una carpeta de ejecución nuevos.

## Validación temporal

- Entrenamiento QVoice desde 2024; periodos principales febrero–julio de 2025 y agosto de 2025–enero de 2026.
- Selección L2 por Brier mensual en los últimos tres intervalos cuyo final se observó antes del inicio calendario del periodo. Las referencias de las interacciones se calculan sólo en entrenamiento.
- Cohorte general idéntica entre B, disponibilidad y respuestas. Las personas sin QVoice permanecen en la evaluación.
- Cohorte con respuestas completas como análisis adicional cuando cumple los mínimos de publicación.
- PR-AUC con empates agrupados, lift del decil, Brier y calibración general y del quintil superior. La reproducción histórica B mantiene el cálculo original para verificar sus resultados.
- Bootstrap pareado por persona: una multiplicidad para todas sus observaciones y para todos los modelos; 500 réplicas e intervalos del 95%. La incertidumbre es condicional a los modelos ajustados.
- Una variante es prometedora si mejora PR-AUC y lift en ambos periodos principales, no empeora el promedio de Brier y errores de calibración, y cumple lo mismo frente al control de disponibilidad. Con menos de dos periodos principales completos evaluables se informa evidencia temporal insuficiente.

## Conciliación y trazabilidad

Los SQL `qvoice_model_<concepto>_20261006.sql` se ejecutan con SQLite sobre métricas agregadas actuales; no representan tablas ficticias de HRDA. El enlace a HRDA se ejecuta desde `qvoice_model_engineering_join_20261006.sql`. Las llaves sólo se incorporan al SQL en memoria; se conserva el hash del statement ejecutado y el template, sin guardar el SQL expandido.

La evidencia registra por separado la población de Engineering, la plantilla original del playbook y los participantes del Excel. En la primera ejecución, la plantilla actual de los baselines de 2024 y 2025 tiene una persona menos que los JSON históricos. `qvoice_model_baseline_reconciliation_20261006.sql` confirma los conteos actuales con el filtro original. Las diferencias permanecen visibles y no elevan scores.

Los datos de 2026 se describen hasta la última foto conocida al corte del 7 de septiembre; no se anualizan. Los números de los gráficos tienen como máximo un decimal; los JSON conservan la precisión necesaria para auditar.

## Pruebas

```powershell
.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_qvoice_model_experiment.py -v
.venv\Scripts\python.exe -B -m unittest discover -s .codex/skills/evaluate-attrition-variable/tests -p test_traceable_assessment.py -v
```

Las pruebas cubren disponibilidad y vencimiento, reemplazo de wave, continuidad laboral, fechas efectivas de etiquetas, duplicados, valores faltantes y 255, las seis bandas, la cohorte de la ablación, Heartbeat, métricas con empates, incertidumbre pareada y la comparación completa con datos sintéticos. Cada workbook pasa el validador del contrato de tres hojas y de comentarios/rationales por score.
