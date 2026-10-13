# Entrada transfer_12m

Pregunta: ¿la entrada existe y evita contradicciones en persona-snapshot?

Motivo: evitar que MAX o una unión resuelvan silenciosamente versiones incompatibles.

Método: SQL `queries/audits/engineering_model_c_transfer_12m_20261008.sql`. Resultado: **pass**.

Impacto en score: ninguno; no es una reevaluación de assessment.

Concepto e historia: Evento con flag, fecha efectiva en la ventana previa, observado a más tardar en t y en el episodio laboral. No asumir que sólo representa IOS voluntario. Se consulta el valor de cada foto de 2020–2026.

Regla previa: Población >0; cero celdas contradictorias. Eventos: populated es prevalencia, no cobertura. Faltantes: categoría explícita. No se asignan scores.

Métricas observadas: ver JSON agregado anual adjunto. Acción: habilitar la representación conservadora para el experimento.
