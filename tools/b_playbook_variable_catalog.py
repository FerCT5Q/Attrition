"""Diccionario del tratamiento efectivo de variables; no modifica el modelo."""
from __future__ import annotations

BASE_SQL = 'queries/profiles/engineering_model_c_qvoice_person_month_20261008.sql'
HISTORY_SQL = 'queries/profiles/engineering_model_d_history_person_month_20261010.sql'
PENDING_SQL = 'queries/profiles/engineering_b_incremental_pending_person_month_20261011_v2.sql'
CATEGORIES_SQL = 'queries/profiles/engineering_b_v11_categories_person_month_20261011_v2.sql'
GRADE_SQL = 'queries/profiles/engineering_b_v11_grade_entry_person_month_20261011.sql'
HIERARCHY_SQL = 'queries/profiles/engineering_b_v11_hierarchy_person_month_20261011_v3.sql'
MANAGER_SQL = 'queries/profiles/engineering_b_v11_manager_history_person_month_20261011_v3.sql'
UNKNOWN = '(unknown)'
UNCONFIRMED = '(historia no confirmada)'
BEFORE = '(antes de la fuente)'
TENURE = ['<1 year','1-2 years','2-3 years','3-5 years','5-10 years','10+ years']
FIVE_TIME = ['<1 year','1-2 years','2-3 years','3-5 years','5+ years']
Q_MISSING = ['no_available_wave','no_linked_row','different_employment_episode',
             'missing','question_absent','sentinel_255','invalid']
Q_AGG_MISSING = ['no_available_wave','no_linked_row','different_employment_episode','missing']
Q_COMMENT_MISSING = ['no_available_wave','no_linked_row','different_employment_episode','duplicate']
B_LABELS = {
    'level_grouped':'Nivel agrupado', 'tenure_playbook_band':'Antigüedad desde ingreso original',
    'calendar_month':'Mes calendario', 'manager_changes_12m':'Cambios de manager en 12 meses',
    'team_exits_12m':'Salidas del equipo en 12 meses', 'direct_reports_band':'Reportes directos',
    'time_since_promotion_band':'Tiempo desde última promoción', 'rehire':'Recontratación',
    'level_x_tenure':'Interacción: nivel y antigüedad',
    'tenure_x_manager_changes':'Interacción: antigüedad y cambios de manager',
}


def catalog(config, qmetadata):
    rows = {}

    def add(feature, kind, fields, raw, values, transformation, missing, consideration,
            query=BASE_SQL, known='Valor o evento disponible en la propia foto t.', sources=None):
        rows[feature] = {
            'feature':feature, 'label':config['feature_labels'].get(feature,B_LABELS.get(feature,feature)),
            'input_type':kind, 'source_fields':fields, 'source_values':raw,
            'values_before_pooling':values, 'transformation':transformation,
            'missing_and_default':missing, 'known_at':known, 'considerations':consideration,
            'sources':sources or [query],
        }
        return rows[feature]

    add('level_grouped','Categoría nominal',['level_grouped'],
        'Etiqueta agrupada registrada; vocabulario abierto, sin recodificarla como número.',
        ['Etiquetas registradas de level_grouped',UNKNOWN],
        'TRIM; blanco se convierte en nulo. Se conserva la etiqueta de la foto. No se añaden ni fusionan niveles de B en esta ronda.',
        'Nulo o blanco → (unknown). La referencia se aprende en cada entrenamiento.',
        'Es el nivel agrupado de B; no se sustituye por compensation_grade ni por job_level_primary_position.')
    add('tenure_playbook_band','Numérica transformada en bandas nominales',
        ['original_hire_date','fis_mo_end_dt'],'Fecha original de ingreso y fecha de foto.',TENURE+[UNKNOWN],
        'DATEDIFF(month, original_hire_date, t); cortes 12, 24, 36, 60 y 120. Cuenta fronteras de mes calendario, no días/365.',
        'Fecha faltante o posterior a t → (unknown). No se imputa cero.',
        'Antigüedad desde ingreso original, no desde la última recontratación. Las seis bandas se conservan como parte de B.')
    add('calendar_month','Calendario categórico',['snapshot_date'],
        'Mes calendario de la foto, de 1 a 12.',[str(i) for i in range(1,13)],
        'Se extrae dt.month en Python y se convierte a cadena/categoría; no es una variable lineal 1–12.',
        'La foto debe tener fecha válida; no se define una imputación de mes.',
        'Es la única entrada que avanza al calcular el riesgo acumulado de los próximos seis meses; RH y QVoice se mantienen en sus valores de t.',
        sources=[BASE_SQL,'tools/b_incremental_data.py','tools/engineering_model_c.py'])
    add('manager_changes_12m','Conteo transformado en categoría',
        ['manager_change','manager_change_date','fis_mo_end_dt'],
        'Flag de evento y fecha registrada de cambio. Se cuentan fechas distintas.', ['0','1','2+'],
        'Cuenta manager_change=1 con fila conocida ≤t y fecha en (t−12 meses,t]; agrupa cero, uno o dos y más.',
        'Sin evento enlazado → 0 por COALESCE. No se crea un estado de ausencia de manager para este conteo.',
        'Cero significa ningún cambio registrado bajo esta regla, no prueba una carrera completa sin cambios. Se conserva el término de B.')
    add('team_exits_12m','Conteo transformado en categoría',
        ['term_type','term_date','manager_employee_id','fis_mo_end_dt'],
        'Salidas VOLUNTARY y manager en la última foto activa anterior al evento, dentro de tres meses.',
        ['0','1','2+',UNKNOWN],
        'Asigna cada salida al manager previo; cuenta eventos de otras personas bajo el manager actual de la persona focal, en (t−12 meses,t], conocidos ≤t. Agrupa 0/1/2+.',
        'Sin manager actual → (unknown). Con manager y sin salidas enlazadas → 0.',
        'No equivale a todas las salidas de un equipo fijo ni a la tasa individual de salida. Los identificadores sólo enlazan dentro de SQL.')
    add('direct_reports_band','Conteo transformado en categoría',
        ['reg_non_intern_dir_reports'],'Conteo directo regular/no intern registrado en la foto.',
        ['0','1-5','6+',UNKNOWN],
        'Después de separar nulos y cero, valores ≤5 van a 1-5; el resto va a 6+. La transformación no añade un filtro separado para negativos.',
        'Nulo → (unknown). Cero es un valor observado distinto.',
        'Describe los reportes directos de la persona focal; es distinto del tamaño del equipo de su manager.')
    add('time_since_promotion_band','Historia de eventos transformada en categoría',
        ['is_promo','promotion_date','service_date','fis_mo_end_dt'],
        'Promociones registradas, fecha de servicio y foto mensual.',
        ['promo <1 year','promo 1-2 years','promo 2-3 years','promo 3+ years',
         'sin promo en historial','sin promo, contratado <1 year','sin promo, contratado 1-3 years',
         'sin promo, contratado 3+ years',UNKNOWN],
        'Busca la última promotion_date con is_promo=1, fila y evento ≤t y evento ≥service_date cuando existe. DATEDIFF(month) determina las bandas de promoción. Si no hay promoción, usa tiempo desde service_date y separa service_date anterior a 2020-08-01.',
        'Sin promoción no se imputa una fecha. Sin fecha de servicio válida y sin promoción → (unknown).',
        '“Sin promo en historial” no significa “nunca promovido”. No utiliza promotion_yes_no de Annual Review.')
    add('rehire','Binaria observada con categoría desconocida',
        ['service_date','original_hire_date','fis_mo_end_dt'],'Dos fechas registradas; no se toma directamente is_rehire.',
        ['yes','no',UNKNOWN],
        'Después de los filtros de faltantes y service_date futura: yes cuando service_date > original_hire_date; no en el resto de casos.',
        'Fecha requerida nula o service_date >t → (unknown).',
        'Es la representación de rehire que usa B, inferida de esas fechas. No agrega un filtro separado de original_hire_date futura. Esta ronda la conserva sin redefinirla.')
    for feature, fields in config['interactions'].items():
        add(feature,'Interacción categórica explícita',fields,'Categorías ya preparadas de los dos términos de B.',
            ['Combinaciones observadas a | b cuando ambos difieren de sus referencias','ref'],
            'Construye a | b sólo si ambas categorías difieren de la referencia de sus términos principales; el resto se codifica ref. Después se omite la categoría más frecuente de la interacción.',
            'Los estados desconocidos se tratan como categorías de los términos de origen. Combinación no aprendida → indicadores cero.',
            'Se conservan las dos interacciones de B. Añadir pares o tríos de candidatas no crea interacciones nuevas entre ellas.',
            sources=['tools/engineering_model_c.py','tools/engineering_b_incremental.py'])
    add('prior_experience_band','Numérica transformada en bandas nominales',['prior_qc_work_years'],
        'Años de experiencia previa almacenados; valor numérico.',
        ['<1 year','1-3 years','3-5 years','5-10 years','10+ years',UNKNOWN],
        'Cortes 1, 3, 5 y 10 sobre el campo registrado; no se recalcula una trayectoria laboral externa.',
        'Nulo o negativo → (unknown).','Se prueba el valor registrado, sin afirmar que capture toda la experiencia previa.')
    add('time_at_level_band','Duración derivada, por bandas',
        ['levelentrydate','service_date','fis_mo_end_dt'],'Fechas de entrada al nivel y de servicio.',
        FIVE_TIME+[UNKNOWN,BEFORE],
        'Desde 2022-10-23: DATEDIFF(month, max(levelentrydate, service_date cuando existe), t). Cortes 12/24/36/60.',
        'Antes de 2022-10-23 → (antes de la fuente); entrada al nivel ausente o futura → (unknown).',
        'Es distinta del rol almacenado, del inicio de perfil y de la entrada observada a compensation_grade. La puerta explícita de fecha futura valida levelentrydate; service_date participa en el máximo sin una puerta adicional propia.')
    add('manager_left_6m','Binaria registrada',['term_type','term_date','manager_employee_id','reg_non_intern_dir_reports'],
        'Salida voluntaria de una persona que tenía reportes directos y vínculo con esos reportes antes del evento.',
        ['yes','no'],
        'Identifica manager con reportes en la última foto dentro de 45 días antes de su salida; marca a quienes reportaban entonces y tienen ese evento conocido en (t−6 meses,t].',
        'Sin evento enlazado → no. No se agrega una categoría de cobertura individual.',
        'Es un evento previo de salida del manager, no el riesgo estimado de que el manager salga. Esta fórmula no contiene un filtro adicional de service_date para reiniciar el evento por recontratación.')
    add('layers_band','Numérica almacenada, por categorías',['worker_supervisory_organization_level_from_top'],
        'Capa organizacional numérica registrada.', ['<=6','7','8','9','10+',UNKNOWN,BEFORE],
        'Antes de 2023-03-26 se bloquea la historia. Después se agrupa ≤6, se conservan 7/8/9 y se agrupa ≥10.',
        'Nulo → (unknown); antes de la fuente se conserva como estado distinto.',
        'La capa almacenada no demuestra profundidad hasta un CEO validado; se compara con la jerarquía reconstruida.')
    add('work_arrangement_group','Categoría agrupada',['work_arrangement'],
        'Etiquetas de modalidad registradas; no se exponen motivos sensibles individuales.',
        ['Onsite','Offsite','Interim Modified','otro o desconocido',BEFORE],
        'Desde 2024-08-25: Onsite exacto, prefijos Offsite e Interim Modified. Otras variantes, motivos sensibles y faltantes se agrupan en otro o desconocido.',
        'Antes de la fecha de fuente → (antes de la fuente). El grupo otro o desconocido mezcla otras modalidades y faltantes.',
        'Es la agrupación previa de C; se prueba separada de los tres grupos exactos del V11.')
    add('region','Categoría nominal',['region'],'Etiqueta regional registrada; vocabulario abierto.',
        ['Etiquetas originales de región',UNKNOWN], 'TRIM y conservación de la etiqueta por foto; no se sustituye por país ni mercado.',
        'Nulo o blanco → (unknown).','También sirve como referencia contemporánea del promedio relativo de QVoice; no es una interacción nueva.')
    add('comp_ratio_band','Razón almacenada transformada en bandas',['compa_ratio'],
        'Valor numérico de compa_ratio en su escala almacenada.',
        ['<0.8','0.8-0.9','0.9-1.0','1.0-1.1','1.1-1.2','1.2+',UNKNOWN],
        'Valor positivo; cortes 0.8/0.9/1.0/1.1/1.2, inferiores incluidos y superiores excluidos en bandas intermedias.',
        'Nulo o ≤0 → (unknown).','Se modela la razón registrada por bandas; no se afirma validación de su numerador, denominador o fórmula de origen.')
    add('grade_family','Categoría agrupada',['compensation_grade'],'Código de grado tal como queda tras TRIM.',
        ['R','T','other',UNKNOWN],'Prefijo R → R, prefijo T → T, cualquier otro grado no nulo → other.',
        'Grado nulo/blanco → (unknown).','No representa todos los tracks; pay_track_detail aplica otra regla más detallada.')
    add('acquisition_recorded','Binaria de presencia de registro',['acquisition'],'Etiqueta de adquisición o falta de etiqueta.',
        ['registrada','sin registro'],'Se marca registrada si acquisition no es nulo ni blanco.',
        'Nulo o blanco → sin registro.','Sin registro no prueba contratación orgánica. Se compara presencia con la etiqueta detallada.')
    add('transfer_12m','Binaria de evento con historia desconocida',
        ['is_transferred','transfer_date','service_date','fis_mo_end_dt'],'Transferencia registrada y fecha.',
        ['yes','no',UNCONFIRMED],'Desde 2023-10-23: is_transferred=1 conocido ≤t, fecha en (t−12 meses,t] y no anterior a service_date cuando existe.',
        'Antes de 2023-10-23 → (historia no confirmada); sin evento admisible después → no.',
        'Transferencia mensual registrada es distinta de los seis motivos IOS; ios_12m se excluyó de la selección.')

    # Las restantes representaciones se añaden abajo con su fórmula efectiva.
    _history_and_pending(add, config)
    _playbook_additions(add)
    _qvoice(add, config, qmetadata)
    return rows


def _history_and_pending(add, config):
    for months in [3,6]:
        add(f'manager_changes_{months}m','Conteo transformado en categoría',
            ['manager_change','manager_change_date','fis_mo_end_dt'],
            'Fechas distintas de cambio de manager registrado.', ['0','1','2+'],
            f'Cuenta eventos conocidos en (t−{months} meses,t], con manager_change=1; agrupa 0/1/2+.',
            'Sin eventos enlazados → 0.',
            'Se compara la ventana corta con los doce meses obligatorios de B; no elimina ese término. Esta fórmula no reinicia el conteo por service_date ni por recontratación.',query=HISTORY_SQL)
        add(f'team_exits_{months}m','Conteo transformado en categoría',
            ['term_type','term_date','manager_employee_id','fis_mo_end_dt'],
            'Eventos voluntarios únicos por persona y fecha, asignados a su manager previo.', ['0','1','2+'],
            f'Cuenta eventos de otras personas bajo el manager actual, conocidos ≤t y con fecha en (t−{months} meses,t]; agrupa 0/1/2+.',
            'Sin eventos enlazados → 0, incluso si falta manager; esta versión no tiene categoría explícita de manager desconocido.',
            'Ventana corta de compañeros; no equivale al contexto V11 de seis intervalos con puerta de observabilidad.',query=HISTORY_SQL)
    add('team_exit_recency_12m','Recencia categórica',
        ['term_type','term_date','manager_employee_id'],
        'Última salida voluntaria admisible bajo el manager actual durante doce meses.',
        ['none in 12m','<3m','3-6m','6-12m',UNKNOWN],
        'Busca la fecha máxima conocida; primero >t−3 meses, después >t−6 meses, resto dentro de doce meses.',
        'Sin manager → (unknown); con manager y sin evento → none in 12m.',
        'No usa eventos posteriores a la foto.',query=HISTORY_SQL)
    add('manager_team_size_band','Conteo por bandas',['manager_employee_id','employee_id','fis_mo_end_dt'],
        'Número de reportes regulares activos sin RF360 del manager actual en la foto.',
        ['1-4','5-9','10-14','15-19','20-29','30+',UNKNOWN],
        'Cuenta personas distintas; cortes superiores 4, 9, 14, 19 y 29. El SQL también ubicaría un conteo cero en 1-4.',
        'Manager o conteo nulo → (unknown).',
        'Incluye a la persona focal cuando reporta a ese manager; no es su propio número de reportes directos.',query=HISTORY_SQL)
    add('team_exit_intensity_12m','Tasa derivada por bandas',
        ['manager_employee_id','term_date','term_type','fis_mo_end_dt'],
        'Salidas voluntarias de compañeros y exposición persona-foto del equipo del manager actual.',
        ['0','>0-<0.5','0.5-<1','1+',UNKNOWN],
        '100 × eventos admisibles en doce meses / exposiciones persona-foto del mismo manager en doce meses; cortes 0, 0.5 y 1.',
        'Manager faltante o exposición cero → (unknown); exposición válida sin salidas → 0.',
        'La unidad es salidas por 100 persona-fotos; no es porcentaje anual de personas que salen.',query=HISTORY_SQL)
    for feature,field,title in [('job_family_detail','job_family','familia de puesto'),
                                ('job_family_group','job_family_group','grupo de familia'),
                                ('work_country','country','país laboral'),
                                ('compensation_grade_detail','compensation_grade','grado completo')]:
        add(feature,'Categoría nominal',[field],f'Etiquetas registradas de {title}; vocabulario abierto.',
            [f'Etiquetas normalizadas de {field}',UNKNOWN],
            'UPPER(TRIM(campo)); conserva la etiqueta de la propia foto. No se asigna distancia ordinal entre categorías.',
            'Nulo o blanco → (unknown); el pooling posterior usa sólo entrenamiento.',
            'Los valores concretos que conserva un modelo final se listan en su codificación; el catálogo de origen puede cambiar por fecha.',query=PENDING_SQL)
    add('work_site','Categoría nominal compuesta',['country','office_site'],
        'País laboral y código de sitio; vocabularios abiertos.', ['PAÍS | SITIO',UNKNOWN],
        'UPPER y TRIM en ambos campos; concatena país y sitio para evitar homónimos.',
        'Falta cualquiera de los dos → (unknown).',
        'Un sitio registrado puede representar varias ciudades; no prueba presencia física.',query=PENDING_SQL)
    add('time_in_job_profile_band','Duración derivada por bandas',
        ['time_in_job_profile_start_date','service_date','fis_mo_end_dt'],
        'Fecha de inicio del perfil y service_date en la foto.',FIVE_TIME+[UNKNOWN],
        'DATEDIFF(month, GREATEST(time_in_job_profile_start_date, service_date), t), cortes 12/24/36/60.',
        'Cualquier fecha requerida nula o futura → (unknown).',
        'La implementación de esta ronda usa service_date como ajuste de episodio. No es max_hire_rehire_date; no se debe describir como si usara esa otra columna. Historia observada desde noviembre de 2025.',query=PENDING_SQL)
    add('manager_location_relation','Categoría nominal derivada',
        ['manager_employee_id','country','office_site','city'],
        'Ubicaciones registradas de persona y manager en la misma foto.',
        ['different country','same recorded site','same recorded city','same country',UNKNOWN],
        'Prioridad: países distintos; mismo sitio no nulo; misma ciudad no nula; resto del mismo país. Usa etiquetas normalizadas.',
        'Manager ausente, unión ambigua o país requerido faltante → (unknown).',
        'No calcula distancia ni zona horaria y no demuestra co-presencia física.',query=PENDING_SQL)
    add('within_team_pay_position','Percentil interno transformado en categoría',
        ['fte_annual_base_pay','fte_annual_base_pay_currency_code','country','compensation_grade','manager_employee_id'],
        'Importes positivos y grupos comparables, sólo dentro de SQL; ningún importe individual se exporta.',
        ['lower quarter','middle half','upper quarter','(no comparable group)'],
        'En grupo de misma foto, manager, país, grado y moneda: (rango inicial−1+(tamaño del empate−1)/2)/(n−1). Requiere n≥5. <0.25 → lower quarter, >0.75 → upper quarter; ambos límites quedan en middle half.',
        'Sin grupo válido de cinco o más → (no comparable group).',
        'Se validó el cálculo por pares y empates de forma independiente; no se compara salario exacto entre países ni monedas.',query=PENDING_SQL)
    add('manager_pay_spread_band','Categoría derivada de dispersión',
        ['fte_annual_base_pay','fte_annual_base_pay_currency_code','country','compensation_grade','manager_employee_id'],
        'Mínimo y máximo internos de grupos comparables de al menos dos personas.',
        ['none','some','all','(no comparable group)'],
        'Cada grupo de manager/país/grado/moneda con n≥2 se marca si máximo/mínimo ≥1.10. Por manager y foto: ninguno, algunos o todos sus grupos cumplen.',
        'Sin grupos comparables → (no comparable group).',
        'Es un resumen de grupos comparables del manager, no una banda de salario individual ni una prueba de inequidad.',query=PENDING_SQL)


def _playbook_additions(add):
    add('work_city','Categoría nominal compuesta',['country','city'],
        'País y ciudad laborales registrados; vocabularios abiertos.', ['PAÍS | CIUDAD',UNKNOWN],
        'UPPER(TRIM) de país y ciudad; concatena ambos para distinguir ciudades homónimas.',
        'Falta país o ciudad → (unknown). No se imputa a partir de domicilio.',
        'La ciudad es ubicación laboral registrada. El catálogo efectivo depende de la foto y del pooling de entrenamiento.',query=CATEGORIES_SQL)
    add('labor_market_detail','Categoría nominal',['labor_market'],
        'Etiquetas de mercado laboral registradas; vocabulario abierto.', ['Etiquetas de labor_market en mayúsculas',UNKNOWN],
        'UPPER(TRIM(labor_market)); conserva el detalle por foto.',
        'Nulo o blanco → (unknown).',
        'No sustituye región ni país; no se afirma que sea una medición externa del mercado laboral.',query=CATEGORIES_SQL)
    add('work_arrangement_v11','Categoría nominal agrupada',['work_arrangement'],
        'Etiqueta registrada de modalidad; se omiten los motivos sensibles del diccionario compartible.',
        ['Onsite','Short-Term Remote Work','Other offsite arrangements',UNKNOWN],
        'UPPER/TRIM y normalización de guiones largos a -. ONSITE → Onsite; INTERIM MODIFIED - SHORT-TERM REMOTE WORK → Short-Term Remote Work; cualquier otro valor no nulo → Other offsite arrangements.',
        'Nulo o blanco → (unknown); no se rellena Onsite por defecto. Esta versión no agrega la puerta de fecha fija de work_arrangement_group.',
        'Son los tres grupos del V11. La tercera etiqueta agrupa todos los restantes valores registrados; no valida por sí sola su semántica de trabajo remoto.',query=CATEGORIES_SQL)
    add('acquisition_detail','Categoría nominal',['acquisition'],
        'Etiqueta de adquisición registrada; vocabulario abierto.', ['Etiquetas normalizadas de acquisition','sin registro'],
        'UPPER(TRIM(acquisition)); conserva el detalle no vacío de la foto.',
        'Nulo o blanco → sin registro.',
        'Sin registro no equivale a ingreso orgánico. Se prueba separada de la presencia binaria acquisition_recorded.',query=CATEGORIES_SQL)
    grade_fields=['compensation_grade','max_hire_rehire_date','is_promo','promotion_date','fis_mo_end_dt']
    grade_rule=('Reconstruye cambios de grado entre fotos consecutivas dentro de max_hire_rehire_date: '
                'grados distintos no nulos, intervalo ≤45 días, fila y episodio unívocos. '
                'Un corte de historia invalida entradas anteriores. Sólo usa fotos y confirmaciones conocidas ≤t.')
    add('current_grade_entry_path','Categoría derivada de historia',grade_fields,
        'Grado actual y anterior, episodio y eventos de promoción en la historia mensual.',
        ['promotion confirmed','observed change without registered promotion',UNCONFIRMED],
        grade_rule+' Para una entrada válida, confirma promoción si is_promo=1 con evento entre la foto anterior y la entrada, mismo grado/episodio y registro conocido ≤t.',
        'Sin entrada reconstruible después del último corte de historia → (historia no confirmada).',
        'No identifica contratación directa ni demuestra que un cambio sin promoción registrada sea lateral. No usa compensation_grade_old.',query=GRADE_SQL)
    add('time_since_grade_entry_band','Duración derivada por bandas',grade_fields,
        'Fecha de entrada observada al grado, reconstruida en el episodio vigente.', FIVE_TIME+[UNCONFIRMED],
        grade_rule+' DATEDIFF(month, última entrada válida, t), con cortes 12/24/36/60.',
        'Entrada no reconstruible → (historia no confirmada).',
        'El inicio es la primera foto del cambio observado, no una fecha efectiva exacta del cambio.',query=GRADE_SQL)
    add('pay_track_detail','Categoría nominal extraída',['compensation_grade'],
        'Código completo de grado registrado.', ['Primera letra A–Z de un código con forma letra+número',UNKNOWN],
        'UPPER/TRIM y expresión regular ^[A-Z][0-9]+$. Si cumple, conserva LEFT(grade,1).',
        'Blanco, nulo o código que no cumple la forma → (unknown).',
        'No se limita a R/T ni inventa la interpretación de cada letra. El grado completo se prueba también por separado.',query=GRADE_SQL)
    add('hierarchy_depth_band','Profundidad reconstruida, por categorías',
        ['employee_id','manager_employee_id','active_status','fis_mo_end_dt'],
        'Relaciones persona–manager de la misma foto, sólo como llaves internas.',
        ['0-2','3','4','5','6','7','8','9','10+',UNCONFIRMED],
        'Reconstruye el árbol desde nodos sin manager (profundidad 0), hasta 25 pasos. Exige cadena unívoca sin ciclos y una única raíz entre las cadenas resueltas de Engineering. Agrupa profundidad 0–2 y 10+, conserva 3 a 9.',
        'Cadena sin resolver, ciclo, ambigüedad, profundidad fuera del alcance o múltiples raíces → (historia no confirmada).',
        'El árbol usa trabajadores activos para poder enlazar superiores fuera de Engineering. Una raíz técnica no acredita por sí sola al CEO de negocio; no se exportan identidades.',query=HIERARCHY_SQL)
    manager_fields=['manager_employee_id','term_date','term_type','fis_mo_end_dt',
                    'region','job_family','job_level_primary_position',
                    'max_hire_rehire_date','service_date','original_hire_date']
    manager_rule=('Atribuye cada salida voluntaria al manager en la foto anterior al intervalo; '
                  'sólo eventos conocidos y sin contradicción conocida a t. '
                  'Exposición de empleados regulares activos sin RF360, también fuera de Engineering. '
                  'La variable de la persona focal toma la historia de su manager actual.')
    add('manager_observed_expected6_band','Razón derivada por bandas',manager_fields,
        'Eventos, exposiciones y estratos de los seis intervalos previos completos.',
        ['<0.5x','0.5-1x','1-1.5x','1.5x+',UNCONFIRMED],
        manager_rule+' Calcula esperado por región × familia × nivel detallado × antigüedad de episodio (<1/1–2/2–5/5+). '
        'Tasa del estrato por intervalo si n≥30; si no, tasa global del intervalo. '
        'O/E=(salidas6+60×tasa_global6)/(esperado6+60×tasa_global6). Cortes 0.5/1/1.5.',
        'Requiere feed global desde 2022-10-23 más seis intervalos, seis tasas globales, exposición del manager >0, tasa previa >0 y esperado disponible; si no → (historia no confirmada).',
        'No exige seis intervalos individuales al manager: exige seis intervalos globales y exposición positiva. '
        'El episodio usa max_hire_rehire_date válido; después service_date válido; después original_hire_date válido. No es una calificación causal del manager.',query=MANAGER_SQL)
    add('manager_team_exits6_v11','Conteo de eventos por categoría',manager_fields,
        'Salidas atribuidas al manager en seis intervalos fiscales mensuales anteriores a t.',
        ['0','1','2+',UNCONFIRMED],
        manager_rule+' Agrupa salidas6 en 0/1/2+. Usa intervalos entre fotos, no DATEADD de seis meses calendario.',
        'Sin exposición positiva, sin seis intervalos globales o antes de completar el feed → (historia no confirmada); con soporte y sin salidas → 0.',
        'No es idéntico a team_exits_6m: cambian ventana, atribución y puerta de observabilidad. No exige seis intervalos individuales al manager.',query=MANAGER_SQL)
    add('manager_above_average18','Binaria derivada con historia desconocida',manager_fields,
        'Salidas y exposiciones del manager en dieciocho intervalos previos.',
        ['above benchmark','not above benchmark',UNCONFIRMED],
        manager_rule+' Exige 18 intervalos individuales completos, equipo promedio ≥4 y al menos dos salidas, después del inicio íntegro del feed. '
        'Tasa18=salidas18/exposiciones18×6. Benchmark de managers elegibles=Σsalidas18/Σexposiciones18×6. '
        'Tasa18≥1.3×benchmark → above benchmark; el resto elegible → not above benchmark.',
        'No elegible o benchmark ausente → (historia no confirmada). Menos de dos salidas no se codifica como not above benchmark.',
        'Es un umbral del V11 con denominador ponderado por exposición; no es el simple promedio de tasas ni un juicio sobre el manager.',query=MANAGER_SQL)
    geography_sources=['queries/profiles/engineering_b_v11_timezone_person_month_20261011_v3.sql',
                       'tools/b_v11_geography.py','tools/build_v7_manager_timezone_annual_attrition_evidence.py']
    add('manager_colocation_v11','Binaria derivada con categoría desconocida',
        ['office_site','country','city','manager_employee_id','fis_mo_end_dt'],
        'Sitio y ciudad registrados de persona y manager en la misma foto.',
        ['same recorded site and city','different recorded site or city',UNKNOWN],
        'Normaliza UPPER/TRIM y elimina caracteres fuera de A–Z/0–9; la llave de ciudad combina país y ciudad. Las llaves se mantienen sólo en RAM. '
        'Con unión unívoca y ambos sitios/ciudades presentes, compara simultáneamente igualdad de sitio e igualdad de país-ciudad. Reconcilia con cálculo independiente SQL.',
        'Unión no utilizable o sitio/ciudad requerido faltante → (unknown).',
        'Igualdad de etiquetas registradas no prueba presencia física ni distancia real.',sources=geography_sources)
    add('manager_timezone_relation','Categoría nominal derivada',
        ['office_site','country','city','manager_employee_id','fis_mo_end_dt','catálogo público de oficinas y zonas IANA'],
        'Sitio/ciudad de ambos y zona horaria del catálogo estático; identificadores de ubicación sólo en RAM.',
        ['same recorded site','different site up to 4 hours','different site more than 4 hours',UNKNOWN,'(unmapped geography)'],
        'Normaliza UPPER/TRIM y elimina caracteres fuera de A–Z/0–9; llave de ciudad = país y ciudad. Mismo sitio → same recorded site. '
        'Si difiere: resuelve zona por sitio o ciudad; contradicción entre ambos mappings invalida la zona. '
        'ZoneInfo calcula offset en la fecha de la foto a las 12 UTC, incluido DST; diferencia absoluta ≤240 minutos o >240.',
        'Par no utilizable o sitios faltantes → (unknown). No se resuelve zona → (unmapped geography).',
        'Catálogo público estático de 2026: no acredita historia de direcciones. No modela huso domiciliario ni diferencias horarias a todas las horas del día.',
        known='Ubicación laboral registrada en la foto t; catálogo público de 2026 aplicado retrospectivamente. No se acredita vigencia histórica del mapping en t.',sources=geography_sources)
    add('commute_distance_onsite_v11','Distancia aproximada por bandas nominales',
        ['country','city','office_site','postal_code (sólo componente efímero en RAM)','work_arrangement','catálogos públicos'],
        'Modalidad, ubicación laboral y componente postal; ningún domicilio, postal o distancia individual se persiste.',
        [f'{i}–<{i+1} km' for i in range(30)]+['30+ km',UNKNOWN,'(not onsite)','(unmapped office)','(unmapped postal centroid)'],
        'Sólo Onsite. UPPER/TRIM de componentes; versión postal compacta elimina caracteres fuera de A–Z/0–9. '
        'Resuelve oficinas compatibles con ciudad y país laboral; excluye DAL.B. Busca centroide postal por coincidencia exacta/compacta y prefijos o relleno con ceros específicos del país. '
        'Orden adicional: US prefijo 5; CA/IE prefijo 3; GB prefijos 4/3/2; NL prefijo 4. Rellena a 6 en CN/IN/SG, a 5 en DE/FR/KR y a 7 en JP. '
        'Haversine entre centroide y oficinas; conserva mínimo si hay varias. Reconcilia por producto punto. Cortes de 1 km hasta 30, después 30+.',
        'Otra modalidad válida → (not onsite). Componentes incompletos/ambiguos → (unknown). Oficina o centroide sin mapping tienen estados distintos; no se imputa distancia cero.',
        'Aproximación postal a oficinas de ciudad, no trayecto de commute validado. Todo el mapping observado resolvió por ciudad; no hay país domiciliario estructurado. '
        'Catálogo estático 2026, sin historia de direcciones; el mínimo entre oficinas puede subestimar la distancia. Los valores >500 km permanecen en 30+ y se reportan en el audit agregado.',
        known='Componentes registrados en la foto t; oficinas y centroides de catálogos estáticos usados retrospectivamente. No se acredita la dirección de oficina ni el mapping disponibles históricamente en t.',
        sources=['queries/profiles/engineering_b_v11_commute_inputs_20261011.sql','tools/b_v11_commute.py',
                 'tools/build_global_commute_distance_evidence.py'])
    add('time_in_role_stored_v11','Numérica almacenada transformada en bandas',
        ['time_in_role','fis_mo_end_dt'],'Valor numérico registrado de time_in_role, sin recalcular unidad o fecha de inicio.',
        ['<1','1-<2','2-<3','3-<5','5-<10','10+',UNKNOWN],
        'Cortes numéricos 1/2/3/5/10 exactamente como V11; se modelan bandas nominales.',
        'Nulo, negativo o valores contradictorios por persona-foto → (unknown).',
        'Disponible desde 2025-08-24; no se declara validada su fórmula ni unidad oficial. Se distingue de tiempo en nivel/perfil; la historia interna determina su elegibilidad.',
        query='queries/profiles/engineering_b_v11_stored_role_person_month_20261012.sql')


def _qvoice(add, config, qmetadata):
    import b_v11_qvoice_comments as comments

    sources=[config['source_qvoice_metadata'],config['source_qvoice_config'],
             config['qvoice']['annual_lag_policy'],'tools/qvoice_model_data.py',
             'tools/qvoice_model_experiment.py','tools/qvoice_horizon_calibration.py']
    known=('Política anual: wave 2024 sólo en fotos de 2025; wave 2025 sólo en 2026. '
           'Vigencia de 12 meses, inicio incluido/fin excluido; la wave siguiente reemplaza la anterior aunque falte respuesta. '
           'Se exige continuidad del episodio desde el ancla de la encuesta; wave 2026 reservada para 2027. '
           'Esta política no acredita la fecha real de publicación.')
    missing=('Blanco/nulo → missing; 255 → sentinel_255; fuera de {0,1} o no numérico → invalid; '
             'encabezado ausente → question_absent. Sin enlace, incluidas llaves duplicadas excluidas, → no_linked_row. '
             'Episodio no continuo → different_employment_episode, con prioridad sobre el resto. '
             'Sin wave asignada → no_available_wave. No se imputa v0.')
    for key in [f'M{i:02d}' for i in range(1,34)]+['career']:
        mappings=[]
        for wave in qmetadata['waves']:
            if wave['year'] not in (2024,2025):
                continue
            item=wave['mapping'][key]
            mappings.append({'wave':wave['year'],'file':wave['file'],'sheet':wave['sheet'],
                'header':[wave['headers'][i] for i in item['binary_indices']],
                'source_text':item['base'],
                'model_year':wave['year']+1})
        row=add('qv_'+key,'Binaria favorable registrada con estados de ausencia',
            [f"Wave {w['wave']}: "+' / '.join(w['header']) for w in mappings],
            'Indicador favorable 0/1 almacenado; también puede haber blancos, 255 y valores inválidos. No se recalcula desde la escala ordinal 1–5.',
            ['v0','v1']+Q_MISSING,
            'Correspondencia por texto exacto y encabezado binario unívoco de cada wave; 0 → v0, 1 → v1. '
            'Se codifica como categoría. Se conserva sólo Response Type vacío o EX cuando ese campo existe; se excluyen llaves inválidas o duplicadas.',
            missing,
            ('2024 incluye «Overall,» y las waves posteriores lo omiten; el transporte entre redacciones es exploratorio. '
             'No confundir esta pregunta con qv_M18, sobre entender cómo avanzar profesionalmente.' if key=='career' else
             'Es una de las 33 preguntas comunes; los aliases Q del diccionario no se cuentan como variables adicionales. '
             '0 significa no favorable en el campo binario, no identifica por separado neutralidad y desacuerdo.')+
            ' Se compara contenido contra su disponibilidad emparejada; no se interpreta una asociación como causalidad.',
            known=known,sources=sources)
        row['wave_mapping']=mappings
        row['question_aliases']=sorted(k for k,v in qmetadata['dictionary'].items()
            if any(v['base']==m['source_text'] for m in mappings))
    aggregate_missing=('Si falta alguna de las 33 respuestas binarias válidas → missing (incluye 255, inválida o pregunta ausente). '
        'Sin enlace o llave duplicada excluida → no_linked_row; episodio no continuo → different_employment_episode; '
        'sin wave asignada → no_available_wave. No se promedia sólo lo contestado.')
    add('qv_mean33','Promedio de binarias transformado en bandas',
        [f'qv_M{i:02d}' for i in range(1,34)],'Treinta y tres indicadores favorables 0/1 válidos.',
        ['<50','50–69','70–79','80–89','90–99','100']+Q_AGG_MISSING,
        '100×suma/33, sólo si las 33 respuestas son válidas. Comparaciones enteras exactas para las bandas: '
        '[0,50), [50,70), [70,80), [80,90), [90,100), {100}. Se introducen indicadores de banda, no el promedio continuo.',
        aggregate_missing,
        'Una combinación del promedio con alguna pregunta comparte información de origen; esta ronda permite ese solapamiento y no demuestra que los aportes sean independientes.',
        known=known,sources=sources)
    add('qv_availability','Indicador categórico de disponibilidad',
        ['qv_mean33'],'Estado de completitud del promedio de 33 preguntas.',
        ['available']+Q_AGG_MISSING,
        'Cualquier banda válida de qv_mean33 → available; conserva los estados no válidos del promedio.',
        aggregate_missing,
        'Es control de disponibilidad de datos, no puntuación favorable ni medida pura de participación: una respuesta incompleta no es available. '
        'También se prueba como candidata por sí sola.',known=known,sources=sources+['tools/b_incremental_data.py'])
    add('qv_region_relative','Promedio relativo contemporáneo transformado en bandas',
        [f'qv_M{i:02d}' for i in range(1,34)]+['region','snapshot_date'],
        'Media de las 33 binarias y región de la misma foto, sin outcomes.',
        ['below -1 sd','-1 to 0 sd','0 to 1 sd','above 1 sd','(region too small)','(zero region variance)']+Q_AGG_MISSING,
        'Calcula media/33 entre 0 y 1; z=(media individual−media regional)/desviación poblacional regional (ddof=0) en la misma foto. '
        'Exige al menos 300 respuestas completas en región/foto y desviación >1e-12. Bandas z<−1, −1≤z<0, 0≤z≤1 y z>1. Reconciliación independiente por momentos.',
        'Hereda ausencia de qv_mean33; región/foto con menos de 300 completas → (region too small); desviación ≤1e-12 → (zero region variance).',
        'La referencia incluye a la persona focal y se calcula en cada foto, sin mirar salidas futuras; no es una normalización aprendida sólo en entrenamiento. '
        'La etiqueta de región (unknown), si existiera, forma su propio grupo y no tiene bloqueo adicional por identidad de región.',
        known=known,sources=sources+['tools/b_incremental_data.py'])
    comment_sources=['config/b_playbook_v11_contracts/qvoice-comments.json','tools/b_v11_qvoice_comments.py',
        'tools/build_qvoice_comment_evidence.py','tools/build_qvoice_retention_concerns_evidence.py',
        'tools/build_qvoice_open_text_request_concern_evidence.py',config['source_qvoice_metadata']]
    normal=('Normaliza espacios y casefold; los patrones literales se buscan con límites de palabra. '
            'Se usan taxonomías completas congeladas, sin escoger temas según salidas futuras. ')
    comment_missing=('Sin wave → no_available_wave; sin enlace → no_linked_row; llave repetida → duplicate; '
                     'episodio no continuo → different_employment_episode (tiene prioridad). '
                     'La ausencia de comentario se conserva; no se interpreta como ausencia del tema en una respuesta existente.')
    for feature in comments.FEATURES:
        improvement=feature=='qv_improvement_comment_presence' or feature in comments.RETENTION
        presence=feature in {'qv_comment_presence','qv_improvement_comment_presence'}
        roles=['can_improve','processes_to_improve'] if improvement else ['doing_well','can_improve','processes_to_improve']
        fields=[f'Prompt {role}' for role in roles]
        if presence:
            formula=('Concatena prompts de mejora' if improvement else 'Concatena todos los prompts disponibles')+'; texto normalizado no vacío → v1; vacío → v0.'
            values=['v0','v1']+(['question_absent'] if improvement else [])+Q_COMMENT_MISSING
        elif feature in comments.RETENTION:
            theme=comments.RETENTION[feature][0]
            formula=f'Concatena prompts de mejora; al menos un patrón de TAXONOMY[{theme!r}] → v1; comentario sin patrón → v0; sin comentario → no_comment.'
            values=['v0','v1','no_comment','question_absent']+Q_COMMENT_MISSING
        elif feature in comments.WORKPLACE:
            theme=comments.WORKPLACE[feature][0]
            formula=f'Concatena todos los prompts; al menos un patrón de TAXONOMY[{theme!r}] → v1; texto sin patrón → v0; sin texto → no_comment.'
            if feature=='qv_comment_office':
                formula+=' Antes de buscar menciones de oficina retira la expresión home office.'
            values=['v0','v1','no_comment']+Q_COMMENT_MISSING
        else:
            formula=('En una misma cláusula, exige un patrón objetivo de remoto/híbrido y otro de petición de cambio.'
                     if feature=='qv_remote_hybrid_request' else
                     'En una misma cláusula, exige un patrón objetivo presencial y otro de inquietud de política; retira home office.')
            formula+=' Tras normalizar espacios (incluidos saltos de línea), separa prompts con punto y cláusulas por puntuación; cualquier cláusula que cumple → v1; texto que no cumple → v0; sin texto → no_comment.'
            values=['v0','v1','no_comment']+Q_COMMENT_MISSING
        row=add(feature,'Indicador textual derivado con estados de ausencia',fields,
            'Comentarios de los prompts declarados, procesados sólo en RAM. No se publican textos ni ejemplos individuales.',
            values,normal+formula,
            comment_missing+(' Si ningún prompt de mejora existe → question_absent.' if improvement else ''),
            '2024 tiene doing_well y can_improve; processes_to_improve aparece desde 2025. '
            'Las menciones pueden pertenecer a varios temas y no prueban sentimiento, intención de salida ni causalidad. '
            'Patrones de palabras pueden producir falsos positivos/negativos; se contrasta contenido con disponibilidad emparejada.',
            known=known,sources=comment_sources)
        row['prompt_roles']=roles


def exclusions():
    """Conceptos sin columna modelada; no inventa valores ni efectos estimados."""
    return [
        {'id':'ios','label':'Movimientos IOS','view_ids':['slide-5'],
         'source':'hrda.workers_ios_transfers',
         'source_fields':['business_process_reason','effective_date','timestamps de carga/modificación'],
         'source_values':'Seis motivos descriptivos de movimiento; no se exporta aquí un dominio de empleados.',
         'proposed_type':'Eventos por motivo; la variante antigua ios_12m también se excluyó.',
         'transformation':'No se construye columna seleccionable en esta ronda; no se imputa no movimiento.',
         'history':'Las cargas y modificaciones actuales son de 2026-10-11; no acreditan disponibilidad de cada evento en las fotos anteriores.',
         'decision':'Excluida antes de selección','reason':'No se verificó conocimiento histórico de las resoluciones IOS.',
         'action':'Obtener historia de versiones o calendario oficial de disponibilidad antes de modelar eventos as-of.',
         'evidence':['v11-ios-knowledge.json'],
         'documentation':['docs/variables/ios-movement/b-model-v11-20261011.md']},
        {'id':'applications','label':'Solicitudes de empleo','view_ids':['slide-3'],
         'source':'hrda.applications; alternativa hrda.job_applications_vw',
         'source_fields':['fechas de solicitud','llave de enlace (sólo dentro de SQL)'],
         'source_values':'Eventos de solicitudes; no se exportan requisiciones ni datos de postulantes.',
         'proposed_type':'Presencia/conteo de solicitudes anteriores a la foto.',
         'transformation':'No se construye columna seleccionable; la ausencia de feed o enlace no se convierte en cero.',
         'history':'applications termina el 2024-10-29 y no tiene eventos de marzo–septiembre de 2026. La vista alternativa llega a 2026, sin historia verificada de enlace y completitud.',
         'decision':'Excluida antes de selección','reason':'Falta continuidad del feed exacto V11 y evidencia temporal suficiente de la alternativa.',
         'action':'Reconstruir fuente histórica y observabilidad del enlace para distinguir ninguna solicitud de dato no disponible.',
         'evidence':['v11-applications-history.json','v11-applications-metadata.json'],
         'documentation':['docs/variables/more-than-3-job-applications/b-model-v11-20261011.md']},
        {'id':'engineering','label':'Engineering frente a otras funciones','view_ids':['slide-15'],
         'source':'hrda.post_hire_monthly_worker_dtls','source_fields':['eng_or_noneng'],
         'source_values':'Engineering es el único valor dentro de la población seleccionada.',
         'proposed_type':'Filtro de población; sería categórica fuera de esta población.',
         'transformation':"TRIM(eng_or_noneng)='Engineering' se usa para filtrar; no se agrega una columna constante al modelo.",
         'history':'Se aplica el mismo filtro en cada foto de la comparación.',
         'decision':'Constante dentro de la población','reason':'No permite distinguir riesgos entre personas de Engineering.',
         'action':'Mantener como criterio de población; una comparación entre funciones sería otra población/modelo.',
         'evidence':[],'documentation':[]},
        {'id':'gender','label':'Género','view_ids':['slide-13'],
         'source':'hrda.post_hire_monthly_worker_dtls','source_fields':['gender'],
         'source_values':'Etiquetas protegidas no enumeradas en un entregable presentation.',
         'proposed_type':'Atributo protegido, no autorizado como predictor.',
         'transformation':'No se incorpora al diseño, no se codifica y no se estima un efecto.',
         'history':'La autorización de procesamiento excluye atributos protegidos como features en toda la ronda.',
         'decision':'Fuera de autorización de predicción','reason':'La autorización vigente excluye su uso como predictor; no es un resultado de desempeño.',
         'action':'Conservar fuera del modelo bajo la autorización vigente.',
         'evidence':[],
         'documentation':['config/attrition_model_in_memory_training_authorization_20261001.json']},
        {'id':'heartbeat','label':'Heartbeat exacto de QVoice','view_ids':['slide-26'],
         'source':'Workbooks QVoice y diccionario de encuesta','source_fields':['scale_Q1 … scale_Q53'],
         'source_values':'Escalas ordinales 1, 2, 3, 4, 5; blanks/255/otros inválidos fuera del dominio.',
         'proposed_type':'Signo relativo de cada pregunta respecto al promedio personal de la escala.',
         'transformation':'Definición propuesta: signo de pregunta−promedio personal; requiere las 53 columnas y al menos 38 respuestas válidas. No se calcula como candidata en esta ronda.',
         'history':'2024 tiene cero escalas ordinales reconocidas; 2025 tiene 52 de 53 y falta Q42. La wave 2026 sólo corresponde a 2027.',
         'decision':'Excluida antes de selección','reason':'No se dispone de la estructura exacta requerida para las waves elegibles.',
         'action':'Recuperar la estructura faltante o definir y validar una medida diferente; no cambiar silenciosamente el denominador.',
         'evidence':['v11-heartbeat-headers.json'],
         'documentation':['docs/variables/qvoice-model/b-heartbeat-v11-20261012.md']},
        {'id':'annual_review','label':'Flag de promoción de Annual Review','view_ids':['slide-34'],
         'source':'hrda.annual_review_report','source_fields':['promotion_yes_no','cycle_name','grade','last_modified_date','airflow_execution_date'],
         'source_values':'YES/NO después de UPPER/TRIM; ciclos AR20–AR25.',
         'proposed_type':'Binaria por persona y ciclo, enlazada al último ciclo conocido.',
         'transformation':'El audit normaliza YES/NO; no se traslada este flag al modelo. La promoción is_promo de B permanece como concepto diferente.',
         'history':'AR20–AR24 tienen carga/modificación 2025-06-25; AR25, 2025-11-09. No se acreditó el calendario original de publicación ni versiones por ciclo.',
         'decision':'Representación exacta excluida; concepto parcialmente cubierto',
         'reason':'El grain y el dominio pasan el control técnico, pero esos timestamps no habilitan usar el flag en años anteriores.',
         'action':'Obtener publicación/versiones históricas; conservar promoción de B y probar por separado track y entrada observada al grado.',
         'evidence':['v11-annual-review-history.json'],
         'documentation':['docs/variables/promotion-history-by-compensation-grade/b-model-annual-review-v11-20261012.md']},
        {'id':'talent','label':'Talent index','view_ids':['slide-50'],
         'source':'hrda.master_talent_index','source_fields':['metadata de columnas y timestamps técnicos'],
         'source_values':'No se extrae el dominio individual del índice: la revisión de esta ronda se detuvo en metadata.',
         'proposed_type':'Índice almacenado; escala, fórmula y versiones sin acreditar para uso temporal.',
         'transformation':'Sin columna de modelo, sin imputación, bandas ni efecto estimado.',
         'history':'Una tabla con 64 columnas y tres timestamps técnicos; no se identificó fecha de negocio ni snapshot del índice.',
         'decision':'Excluida antes de selección','reason':'No hay ancla de negocio suficiente para reproducir lo conocido en cada foto.',
         'action':'Definir fórmula, grain, fecha de disponibilidad e historia de versiones antes de probarlo.',
         'evidence':['v11-talent-metadata.json'],
         'documentation':['docs/variables/talent-index/b-model-v11-20261012.md']},
    ]
