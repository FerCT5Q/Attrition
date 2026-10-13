# Casos límite sintéticos de jerarquía

Modo `presentation`. Prueba de límites de la implementación, no evidencia HR.

Pregunta: El SQL distingue árbol válido, manager ausente, auto-ciclo, ciclo de dos nodos, varias raíces y profundidad mayor de 25.

Motivo: Verificar la reconstrucción con un oráculo independiente antes de modelar.

Tipo: `hierarchy`. Población: Grafos ficticios; no son datos de empleados. Grain: nodo sintético.

Conocimiento: Cada grafo se evalúa por separado en su fecha ficticia. Ventana: Seis escenarios sintéticos.

Método y regla: Cero diferencias frente al recorrido independiente en Python. SQL: `queries/audits/engineering_b_v11_hierarchy_synthetic_v3_20261011.sql`.

Resultado: **pass**. Métricas completas en [v11-hierarchy-synthetic-v3.json](v11-hierarchy-synthetic-v3.json).

Conclusión: Los casos límite probados se comportan como se definió.

Limitación: Los fixtures no sustituyen la auditoría agregada de datos históricos.

Acción: Conservar ambas evidencias con hashes. Impacto en score: ninguno.

Ejecución: 2026-10-12T14:03:35.975688+00:00. SHA256 SQL: `0f0168ab94a060169e06b46e2845c0e307928bf02e5c4dc2cfb8079fec9c83a9`.
