/* Diagnostico agregado de duracion de consultas para la ejecucion RSF.
   Modo presentation. Sin texto SQL, usuarios ni identificadores de consultas. */
SELECT status,
       COUNT(*) AS visible_queries,
       MAX(DATEDIFF(second, start_time, GETDATE())) AS oldest_seconds
FROM sys_query_history
WHERE status IN ('running', 'queued', 'returning')
GROUP BY status
