# Consultas agregadas

- `audits/`: validaciones de esquema, freshness, consistencia y calidad de entrada.
- `profiles/`: consultas que producen las columnas agregadas esperadas por `evaluate-attrition-variable`.

Todas las consultas deben ejecutarse en modo read-only y no deben devolver filas, IDs, categorías protegidas, compensación exacta ni texto libre a nivel empleado.

Para respaldar un score 2 cualitativo, la consulta debe quedar guardada, devolver
métricas agregadas reproducibles y estar citada en el spec v4 junto con fecha,
población, regla de aceptación y resultado.
