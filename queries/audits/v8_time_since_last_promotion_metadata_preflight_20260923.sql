-- Preflight de metadatos para la revisión V8 de Time since last promotion.
-- Propósito: confirmar la disponibilidad y los tipos de los campos necesarios
-- antes de consultar agregados de empleados. No devuelve datos de empleados.
-- Variable: Time since last promotion (derived_feature).
-- Uso: describir la última promoción registrada del episodio vigente y, para
--      quienes no tienen evento registrado, comparar nivel y antigüedad de rol.
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'hrda'
  AND table_name = 'post_hire_monthly_worker_dtls'
  AND column_name IN (
      'employee_id',
      'fis_mo_end_dt',
      'worker_type',
      'employee_type',
      'active_status',
      'is_promo',
      'promotion_date',
      'max_hire_rehire_date',
      'time_in_role',
      'time_in_job_profile_start_date',
      'job_level_primary_position',
      'level_grouped',
      'management_level',
      'term_date',
      'term_type'
  )
ORDER BY ordinal_position;
