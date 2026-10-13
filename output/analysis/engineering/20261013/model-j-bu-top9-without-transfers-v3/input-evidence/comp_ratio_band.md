# Entrada comp_ratio_band

Pregunta: ¿la entrada existe y evita contradicciones en persona-snapshot?

Motivo: evitar que MAX o una unión resuelvan silenciosamente versiones incompatibles.

Método: SQL `queries/audits/engineering_model_c_comp_ratio_band_20261008.sql`. Resultado: **pass**.

Impacto en score: ninguno; no es una reevaluación de assessment.

Concepto e historia: Bandas del valor almacenado; no se afirma fórmula salario/punto medio ni se vuelve a validar ese significado económico. Se consulta el valor de cada foto de 2020–2026.

Regla previa: Población >0; cero celdas contradictorias. Eventos: populated es prevalencia, no cobertura. Faltantes: categoría explícita. No se asignan scores.

Métricas observadas: ver JSON agregado anual adjunto. Acción: habilitar la representación conservadora para el experimento.
