-- Diagnóstico agregado de ejecución, sin texto de consultas ni identidades.
SELECT status,COUNT(*) AS query_count,
       MAX(DATEDIFF(second,starttime,GETDATE())) AS maximum_elapsed_seconds
FROM stv_recents
WHERE user_name=CURRENT_USER
GROUP BY status
