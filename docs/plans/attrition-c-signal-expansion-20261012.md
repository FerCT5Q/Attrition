# Expansión incremental de C con señales V11

## Objetivo

Comprobar si las señales que mejoraron B conservan información incremental al
añadirse al modelo C: ciudad laboral, familia de puesto detallada y dos señales
históricas del manager. La comparación es experimental y se entrega en modo
`presentation`; no publica filas, identificadores ni scores individuales.

## Diseño congelado

Se reutilizan los cuatro cortes externos y las selecciones de variables y L2
archivadas en `output/analysis/engineering/20261008/model-c-v2/selection/`.
Para cada corte se reajusta C y después se reajustan cinco variantes: cada
señal por separado, las dos señales de ubicación y familia juntas, y las dos
señales del manager por separado. Las reglas de grupos permanecen en
antigüedad × salidas del equipo × nivel, con capacidad principal del 30%.

La comparación mide Brier, log-loss, PR-AUC, lift, captura al 30% y error de
grupo en los mismos cortes temporales. Se calcula un intervalo pareado por
persona para cada variante, conservando las observaciones mensuales juntas.
Los resultados externos no se usan para volver a seleccionar C ni para
promover una variante.

## Señales probadas

- `work_city`: ciudad laboral categórica preparada en V11.
- `job_family_detail`: familia de puesto detallada categórica preparada en V11.
- `manager_observed_expected6_band`: salidas observadas frente a esperadas del
  manager, en seis intervalos.
- `manager_team_exits6_v11`: salidas bajo el manager actual, en seis intervalos.

Las dos últimas se usan sólo con las bandas y reglas temporales ya congeladas
en la evidencia V11. No se reconstruyen filas ni se calculan scores fuera de
memoria.

## Regla de lectura

Una señal se considera candidata a una ronda posterior si mejora de forma
consistente la pérdida y/o la captura, sin empeorar materialmente el error de
grupo. Una mejora sobre C no se interpreta como causalidad ni como garantía de
mejora sobre C + QVoice.

La configuración ejecutable está en
`config/engineering_c_signal_expansion_20261012.json`.
