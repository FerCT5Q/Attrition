"""Congela el diseño y las consultas de C; no consulta datos de empleados."""
from pathlib import Path
import json
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]


def put(path, text):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


BASE = ['level_grouped', 'tenure_playbook_band', 'calendar_month',
        'manager_changes_12m', 'team_exits_12m', 'direct_reports_band',
        'time_since_promotion_band', 'rehire', 'level_x_tenure', 'tenure_x_manager_changes']
EXTRA = ['prior_experience_band', 'time_at_level_band', 'manager_left_6m', 'ios_12m',
         'layers_band', 'work_arrangement_group', 'region', 'comp_ratio_band',
         'grade_family', 'acquisition_recorded', 'transfer_12m']


def main():
    config = {
        'run_id': 'engineering-model-c-20261008-v1', 'reporting_mode': 'presentation',
        'output': 'output/analysis/engineering/20261008/model-c-v1',
        'authorization': 'config/attrition_model_in_memory_training_authorization_20261001.json',
        'query': 'queries/profiles/engineering_model_c_person_month_20261008.sql',
        'knowledge_boundary': '2026-09-07', 'training_start': '2020-07-26',
        'qvoice_included': False, 'base_features': BASE, 'candidate_features': BASE + EXTRA,
        'interactions': {'level_x_tenure': ['level_grouped', 'tenure_playbook_band'],
                         'tenure_x_manager_changes': ['tenure_playbook_band', 'manager_changes_12m']},
        'outer_starts': ['2024-02-01', '2024-08-01', '2025-02-01', '2025-08-01'],
        'outer_snapshots': 6, 'inner_origins_months_before': [15, 9], 'inner_snapshots': 3,
        'screening_inverse_penalties': [0.003, 0.01, 0.03, 0.1, 0.3, 1.0],
        'ridge_grid': [0.1, 1.0, 10.0], 'penalty_cell_scale': 8.0,
        'selection': {'maximum_relative_brier_worsening': 0.0,
                      'minimum_relative_pr_auc': 0.99, 'minimum_relative_lift10': 0.99,
                      'log_loss_parsimony_tolerance': 0.002,
                      'description': 'L1 mensual en el entrenamiento interno más antiguo; conjuntos completos de variables, jerarquía de interacciones; refit cloglog L2; selección por log-loss R6 sujeto a Brier y ranking; menor número de variables dentro de 0,2% del mínimo.'},
        'groups': {'depth': 3, 'maximum_leaves': 8, 'minimum_training_people': 300,
                   'target_high_fraction': 0.2, 'minimum_people_per_snapshot': 30,
                   'minimum_events_for_rates': 30},
        'decision': {'minimum_log_loss_improvement': 0.005,
                     'minimum_relative_pr_auc_gain': 0.02, 'minimum_relative_lift10_gain': 0.02,
                     'minimum_winning_folds': 3, 'maximum_group_mae_worsening_pp': 0.1,
                     'maximum_high_group_error_worsening_pp': 0.1,
                     'description': 'Ganar log-loss >=0,5%; Brier no peor; PR-AUC y lift10 >=2% mejores y ganar ambos en >=3/4 periodos; error en los mismos grupos y grupo alto de C no empeora >0,1 pp. Además, límite superior IC95 de diferencia de log-loss <0 para evidencia concluyente.'},
        'bootstrap_repetitions': 500, 'seed': 20261008,
        'pca': 'No se usa: selección supervisada sobre categorías originales conserva interpretación; PCA maximiza varianza de X y no la señal de salida.',
        'limitations': ['Evaluación anidada retrospectiva; estos años ya se habían explorado. No es una confirmación prospectiva independiente.',
                       'IOS usa fecha efectiva; no se conoce la fecha de publicación de cada evento. Los snapshots pueden contener revisiones históricas.',
                       'Las tasas de salida voluntaria son etiquetas binarias de población activa; otras salidas cuentan como no voluntarias. No es un modelo de riesgos competitivos.',
                       'Los intervalos entre snapshots fiscales no tienen siempre la misma duración; se conserva la convención mensual de B.',
                       'Candidatos limitados al inventario y representaciones documentadas; no se afirma óptimo global entre todas las combinaciones posibles.'],
    }
    put('config/engineering_model_c_20261008.json', json.dumps(config, indent=2, ensure_ascii=False)+'\n')
    sql = (ROOT/'queries/profiles/engineering_person_month_features_playbook_v2_20261003.sql').read_text(encoding='utf-8')
    sql = sql[sql.index('WITH params AS'):]
    sql = sql.replace('WHERE c.next_snapshot_date IS NOT NULL\n    AND c.snapshot_date >=', 'WHERE c.snapshot_date >=')
    sql = sql.replace('MAX(p.reg_non_intern_dir_reports) AS dir_reports', '''MAX(p.reg_non_intern_dir_reports) AS dir_reports,
    MAX(NULLIF(TRIM(p.region), '')) AS region,
    MAX(p.compa_ratio) AS cr,
    MAX(NULLIF(TRIM(p.compensation_grade), '')) AS grade,
    MAX(CASE WHEN NULLIF(TRIM(p.acquisition), '') IS NOT NULL THEN 1 ELSE 0 END) AS acquisition_recorded''')
    sql = sql.replace('    h.is_promo,', '    h.is_transferred,\n    CAST(h.transfer_date AS DATE) AS transfer_date,\n    h.is_promo,')
    sql = sql.replace('(h.is_promo = 1 OR h.manager_change = 1)', '(h.is_promo = 1 OR h.manager_change = 1 OR h.is_transferred = 1)')
    sql = sql.replace('voluntary_events AS (', '''transfer_events AS (
  SELECT p.snapshot_date, p.employee_id, 1 AS transfer_12m
  FROM pop p INNER JOIN history h ON h.employee_id = p.employee_id
   AND h.is_transferred = 1 AND h.row_date <= p.snapshot_date
   AND h.transfer_date > DATEADD(month, -12, p.snapshot_date)
   AND h.transfer_date <= p.snapshot_date
   AND (p.service_date IS NULL OR h.transfer_date >= p.service_date)
  GROUP BY 1, 2
),
voluntary_events AS (''')
    # La fecha en que la salida está registrada evita usar una corrección futura como feature.
    sql = sql.replace('SELECT employee_id, CAST(term_date AS DATE) AS term_date', 'SELECT employee_id, CAST(term_date AS DATE) AS term_date, MIN(CAST(fis_mo_end_dt AS DATE)) AS known_date')
    sql = sql.replace('SELECT employee_id, term_date\n  FROM voluntary_events', 'SELECT employee_id, term_date, known_date\n  FROM voluntary_events')
    sql = sql.replace('SELECT employee_id, term_date, manager_id', 'SELECT employee_id, term_date, manager_id, known_date')
    sql = sql.replace('      e.term_date,\n      w.manager_employee_id', '      e.term_date, e.known_date,\n      w.manager_employee_id')
    sql = sql.replace('AND x.term_date <= p.snapshot_date', 'AND x.term_date <= p.snapshot_date\n   AND x.known_date <= p.snapshot_date')
    sql = sql.replace('SELECT e.employee_id AS leaver_id, e.term_date, MAX(c.snapshot_date)', 'SELECT e.employee_id AS leaver_id, e.term_date, MIN(e.known_date) AS known_date, MAX(c.snapshot_date)')
    sql = sql.replace('SELECT s.leaver_id, s.term_date, s.ref_snapshot', 'SELECT s.leaver_id, s.term_date, s.ref_snapshot, MIN(s.known_date) AS known_date')
    sql = sql.replace('SELECT DISTINCT r.employee_id, l.term_date', 'SELECT DISTINCT r.employee_id, l.term_date, l.known_date')
    sql = sql.replace('AND r.term_date <= p.snapshot_date', 'AND r.term_date <= p.snapshot_date\n   AND r.known_date <= p.snapshot_date')
    sql = sql.replace('    p.dir_reports,', '    p.dir_reports, p.region, p.cr, p.grade, p.acquisition_recorded,\n    COALESCE(tr.transfer_12m, 0) AS transfer_12m,')
    sql = sql.replace('  LEFT JOIN last_promo lp', '  LEFT JOIN transfer_events tr ON tr.snapshot_date = p.snapshot_date AND tr.employee_id = p.employee_id\n  LEFT JOIN last_promo lp')
    sql = sql.replace('SELECT\n  f.snapshot_date,', "SELECT\n  f.snapshot_date,\n  MD5(CAST(f.employee_id AS VARCHAR) || '__RUN_SALT__') AS person_key,\n  f.next_snapshot_date AS label_end,")
    extra = '''  COALESCE(f.region, '(unknown)') AS region,
  CASE WHEN f.cr IS NULL OR f.cr <= 0 THEN '(unknown)'
       WHEN f.cr < 0.8 THEN '<0.8' WHEN f.cr < 0.9 THEN '0.8-0.9'
       WHEN f.cr < 1.0 THEN '0.9-1.0' WHEN f.cr < 1.1 THEN '1.0-1.1'
       WHEN f.cr < 1.2 THEN '1.1-1.2' ELSE '1.2+' END AS comp_ratio_band,
  CASE WHEN f.grade LIKE 'R%' THEN 'R' WHEN f.grade LIKE 'T%' THEN 'T'
       WHEN f.grade IS NULL THEN '(unknown)' ELSE 'other' END AS grade_family,
  CASE WHEN f.acquisition_recorded = 1 THEN 'registrada' ELSE 'sin registro' END AS acquisition_recorded,
  CASE WHEN f.snapshot_date < DATE '2023-10-23' THEN '(historia no confirmada)'
       WHEN f.transfer_12m = 1 THEN 'yes' ELSE 'no' END AS transfer_12m,
'''
    sql = sql.replace('  CASE\n    WHEN f.next_snapshot_date >', extra+'  CASE\n    WHEN f.next_snapshot_date IS NULL OR f.next_snapshot_date >')
    put(config['query'], '/* C y control B: sólo memoria, autorización 20261001. Salt efímero.\n   Se conserva la última foto sin etiquetas. Salidas como features sólo tras su primera foto registrada.\n   No QVoice, IDs publicables, compensación exacta ni caché de filas. */\n'+sql)
    meta = '''SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'hrda'
 AND table_name IN ('post_hire_monthly_worker_dtls', 'workers_ios_transfers')
 AND column_name IN ('employee_id','fis_mo_end_dt','region','compa_ratio','compensation_grade',
 'acquisition','is_transferred','transfer_date','level_grouped','original_hire_date','service_date',
 'levelentrydate','prior_qc_work_years','worker_supervisory_organization_level_from_top',
 'work_arrangement','reg_non_intern_dir_reports','is_promo','promotion_date','manager_change',
 'manager_change_date','manager_employee_id','term_date','term_type','effective_date',
 'business_process_reason','worker_type','employee_type','active_status','is_rf360_yes_no','eng_or_noneng')
ORDER BY table_name, column_name
'''
    put('queries/audits/engineering_model_c_metadata_20261008.sql', meta)
    # Contratos acotados: no constituyen nuevos scores de assessment.
    contracts = {
      'region': ('direct_field', "NULLIF(TRIM(region), '')", 'Etiqueta regional almacenada; contexto de mercado, no localización personal.'),
      'comp_ratio_band': ('precomputed_metric', "CASE WHEN compa_ratio > 0 THEN 'positivo' END", 'Bandas del valor almacenado; no se afirma fórmula salario/punto medio ni se vuelve a validar ese significado económico.'),
      'grade_family': ('grouped_mapping', "CASE WHEN compensation_grade LIKE 'R%' THEN 'R' WHEN compensation_grade LIKE 'T%' THEN 'T' ELSE 'other' END", 'Prefijo literal R/T/otro, no equivalencia a un nivel detallado.'),
      'acquisition_recorded': ('direct_field', "CASE WHEN NULLIF(TRIM(acquisition), '') IS NOT NULL THEN 'registrada' ELSE 'sin registro' END", 'Presencia de adquisición registrada; vacío no demuestra ingreso orgánico.'),
      'transfer_12m': ('derived_feature', "CASE WHEN is_transferred = 1 AND transfer_date IS NOT NULL AND CAST(transfer_date AS DATE) <= CAST(fis_mo_end_dt AS DATE) THEN 'evento fechado' END", 'Evento con flag, fecha efectiva en la ventana previa, observado a más tardar en t y en el episodio laboral. No asumir que sólo representa IOS voluntario.'),
    }
    for name, (kind, expression, meaning) in contracts.items():
        q = f'''/* Contrato de entrada C: {name}. Sólo agregados; no demuestra un score semántico. */
WITH p AS (
 SELECT employee_id, CAST(fis_mo_end_dt AS DATE) AS d, {expression} AS v
 FROM hrda.post_hire_monthly_worker_dtls
 WHERE worker_type='Employee' AND employee_type='Regular' AND active_status=1
 AND is_rf360_yes_no=0 AND TRIM(eng_or_noneng)='Engineering' AND employee_id IS NOT NULL
 AND CAST(fis_mo_end_dt AS DATE) BETWEEN DATE '2020-07-26' AND DATE '2026-09-07'
), cells AS (
 SELECT employee_id, d, COUNT(*) AS n, COUNT(DISTINCT v) AS versions,
        MAX(CASE WHEN v IS NOT NULL THEN 1 ELSE 0 END) AS populated
 FROM p GROUP BY 1,2
)
SELECT EXTRACT(year FROM d)::INTEGER AS year, COUNT(*) AS employee_snapshots,
 COUNT(DISTINCT employee_id) AS employee_count,
 SUM(CASE WHEN n>1 THEN 1 ELSE 0 END) AS duplicate_cells,
 SUM(CASE WHEN versions>1 THEN 1 ELSE 0 END) AS contradictory_cells,
 SUM(populated) AS populated_cells
FROM cells GROUP BY 1 HAVING COUNT(DISTINCT employee_id)>=30 ORDER BY 1
'''
        put(f'queries/audits/engineering_model_c_{name}_20261008.sql', q)
    put('config/engineering_model_c_input_contracts_20261008.json', json.dumps({
        name: {'semantic_type': x[0], 'meaning': x[2], 'known_at': 'snapshot t',
               'population': 'Engineering activo, regular, Employee, excluye RF360',
               'grain': 'persona-snapshot; evidencia agregada anual',
               'acceptance': 'Población >0; cero celdas contradictorias. Eventos: populated es prevalencia, no cobertura. Faltantes: categoría explícita. No se asignan scores.',
               'sql': f'queries/audits/engineering_model_c_{name}_20261008.sql'} for name,x in contracts.items()
    }, indent=2, ensure_ascii=False)+'\n')
    requested = yaml.safe_load((ROOT/'config/attrition_43_model_run_request_20260816.yaml').read_text(encoding='utf-8'))['variables']
    mapping = {3:'transfer_12m; ios_12m',6:'team_exits_12m; direct_reports_band (conteos, no tasa)',7:'team_exits_12m',9:'region',11:'work_arrangement_group',13:'rehire (proxy service_date)',14:'prior_experience_band',26:'time_at_level_band',27:'tenure_playbook_band',28:'time_since_promotion_band',29:'time_since_promotion_band + rehire (parcial; no equivalencia completa)',30:'level_grouped',31:'layers_band (valor almacenado; no profundidad reconstruida al CEO)',32:'grade_family (prefijo, no todos los grados)',33:'comp_ratio_band (valor almacenado)',38:'manager_left_6m',39:'manager_changes_12m',40:'manager_changes_12m',42:'transfer_12m, manager_changes_12m y promoción (parcial)'}
    excluded = {1:'Fuente de applications sin enlace completo y autorización operativa; queda pendiente.',2:'Misma limitación de applications.',4:'Geografía representada por región; granularidad de sitio queda fuera de esta búsqueda.',5:'Requiere denominador y grupo comparable de compensación; pendiente.',8:'Granularidad adicional no prioritaria de este experimento; pendiente.',10:'Atributo protegido excluido del predictor.',12:'Constante por definición de población Engineering.',15:'No hay integración histórica aprobada de domicilio/distancia para esta búsqueda.',23:'Fuente externa no integrada temporalmente.',24:'Fuente externa no integrada temporalmente.',25:'Fuente externa no integrada temporalmente.',34:'Join histórico con ubicación de manager pendiente.',35:'Derivación de distancia/tiempo con manager pendiente.',36:'Definición de alto riesgo puede ser circular; no se usa.',37:'La señal utilizada es salida del equipo actual, no reputación histórica de una persona.',41:'Definición e historia de talent index pendientes.',43:'Se evitan etiquetas de líderes e identificadores; jerarquía detallada pendiente.'}
    rows=[]
    for i,v in enumerate(requested,1):
        reason = mapping.get(i) or ('QVoice excluido por instrucción; reservado para C + Q.' if 16<=i<=22 else excluded[i])
        rows.append({'order':i,'variable':v['name'],'status':'candidata o representación parcial' if i in mapping else 'excluida o pendiente','representation_or_reason':reason})
    rows += [{'order':44,'variable':'Adquisición registrada (adición del playbook)','status':'candidata','representation_or_reason':'acquisition_recorded'}, {'order':45,'variable':'Tamaño de equipo directo (adición del playbook)','status':'candidata','representation_or_reason':'direct_reports_band'}]
    put('config/engineering_model_c_inventory_20261008.json',json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
    plan = '''# Modelo C sin QVoice: diseño congelado antes del entrenamiento

## Objetivo y comparación

Mejorar estimación R6, detección de grupos de riesgo e interpretación frente a la receta B.
Modo: `presentation`. No modifica B, B + QVoice ni la presentación. C + Q sólo será una etapa posterior si C mejora.
Se reutiliza la autorización de procesamiento en memoria del 1 de octubre de 2026.

## Selección

Los parámetros exactos están en `config/engineering_model_c_20261008.json`.
Toda variable de B puede retirarse. L1 logístico mensual es únicamente un filtro supervisado:
sus coeficientes no son el modelo final. Sus conjuntos se reajustan como hazard cloglog L2.
Se incluyen también el conjunto completo y B. Los padres de una interacción se conservan si ésta entra.
Las seis penalizaciones L1 generan un recorrido acotado; no se prueban las 2^21 combinaciones.
PCA es compatible con snapshots si se aprende sólo en el pasado, pero aquí no se usa: optimiza
variación de los predictores y dificulta mantener grupos comprensibles. L1 responde a la salida observada.

Cada origen externo contiene dos validaciones internas, 15 y 9 meses antes, de tres snapshots.
Los seis meses de seguimiento interno deben terminar antes del origen externo.
Cada entrenamiento mensual exige `label_end <= origen`; cada evaluación R6 exige seguimiento completo.
L1 y las categorías se aprenden con el entrenamiento interno más antiguo; la comparación interna elige
variables y L2. Después se reajusta sólo con el pasado y se mide en los seis snapshots externos siguientes.
Se evalúa retrospectivamente febrero 2024–enero 2026, con sus seguimientos hasta julio 2026.
No se describen estos años previamente explorados como un holdout virgen.

## Métricas y decisión

Selección por log-loss R6, sujeta a Brier no peor y ranking dentro de 1% de B en validación interna.
Se favorece el conjunto más pequeño dentro de 0,2% del mejor log-loss elegible.
La regla final exige mejora de al menos 0,5% en log-loss; Brier no peor;
PR-AUC y lift10 al menos 2% mejores y ganancias en tres de cuatro periodos;
error medio de grupos y error del grupo alto de C sin empeorar más de 0,1 puntos porcentuales.
Bootstrap por persona para diferencias de pérdidas, conservando la dependencia de snapshots;
no mide incertidumbre macrotemporal. Si el intervalo incluye cero, la mejora queda como indicativa.

## Grupos

Árbol de máximo tres condiciones y ocho hojas, entrenado para resumir el riesgo predicho en la
última foto anterior al origen; mínimo 300 personas por hoja de entrenamiento. Se congela antes
de ver salidas futuras. Variables originales, sin calendario en las reglas.
Grupo alto: hojas ordenadas por riesgo predicho en entrenamiento hasta cubrir al menos 20%.
Se reporta cobertura real porque una hoja completa puede superar ese porcentaje.
B y C se comparan en los mismos grupos de C; también se mide el ranking propio de cada modelo.
Publicación sólo con 30 personas por snapshot y 30 eventos para tasas observadas.

## Datos y alcance

Inventario trazable de las 43 variables más dos adiciones del playbook en
`config/engineering_model_c_inventory_20261008.json`. Las representaciones parciales y exclusiones
son explícitas; no se afirma haber probado cada concepto o combinación.
Las nuevas entradas tienen contratos y SQL agregados por variable. Se ejecutan y cierran secuencialmente.
No es un nuevo assessment v4 ni se asignan scores de disponibilidad o definición.
Comp ratio y capas son campos almacenados: no se afirma haber demostrado su fórmula ni raíz CEO.
Los vacíos de adquisición significan ausencia de registro, no origen orgánico.
Se conserva la última foto sin etiquetas para obtener grupos pronosticados, sin llamarlos observados.
Se exige primera foto de registro <= t para salidas del equipo y manager usadas como features.
Este endurecimiento se aplica a B y C en el mismo frame; el control reproduce la receta de B,
no promete reproducir exactamente sus cifras históricas. IOS carece de fecha de publicación por evento.

## Eficiencia y trazabilidad

Una carga a memoria por lotes, matrices dispersas reutilizadas, predicción R6 analítica,
ninguna caché de personas en disco. Se guardan configuración congelada, hashes de consultas y código,
métricas por periodo, recorrido de selección, coeficientes, reglas y verificación sintética.
Se guarda el modelo final como candidato aunque no supere la regla, identificado como experimental.
'''
    put('docs/plans/attrition-model-c-20261008.md',plan)
    print('Configuración, inventario, contratos y SQL de C preparados; no se consultaron datos.')


if __name__ == '__main__':
    main()
