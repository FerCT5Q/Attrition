# Entrada transfer_history

Pregunta: ¿la entrada existe y evita contradicciones en persona-snapshot?

Motivo: evitar que MAX o una unión resuelvan silenciosamente versiones incompatibles.

Método: SQL `queries/audits/engineering_model_c_transfer_history_20261008.sql`. Resultado: **pass**.

Impacto en score: ninguno; no es una reevaluación de assessment.

Concepto e historia: Comprobar desde cuándo existe el flag de transferencia, porque 2020 y 2021 no contienen eventos fechados. No interpretar fuente ausente como no transferencia. Se consulta el valor de cada foto de 2020–2026.

Regla previa: Dominio binario; registrar primer snapshot observable y reservar 12 meses antes de codificar ausencia de evento. Cero eventos previos exige investigar cobertura del flag.

Métricas observadas: ver JSON agregado anual adjunto. Acción: habilitar la representación conservadora para el experimento.
