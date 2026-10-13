# Entrada grade_family

Pregunta: ¿la entrada existe y evita contradicciones en persona-snapshot?

Motivo: evitar que MAX o una unión resuelvan silenciosamente versiones incompatibles.

Método: SQL `queries/audits/engineering_model_c_grade_family_20261008.sql`. Resultado: **pass**.

Impacto en score: ninguno; no es una reevaluación de assessment.

Concepto e historia: Prefijo literal R/T/otro, no equivalencia a un nivel detallado. Se consulta el valor de cada foto de 2020–2026.

Regla previa: Población >0; cero celdas contradictorias. Eventos: populated es prevalencia, no cobertura. Faltantes: categoría explícita. No se asignan scores.

Métricas observadas: ver JSON agregado anual adjunto. Acción: habilitar la representación conservadora para el experimento.
