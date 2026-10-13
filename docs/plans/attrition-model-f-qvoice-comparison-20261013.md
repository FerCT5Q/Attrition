# Comparacion F + QVoice - 13 de octubre de 2026

## Objetivo

Medir si `work_city`, una senal que mejoro modestamente a C sin QVoice,
aporta informacion adicional al incorporarse a `C + QVoice`. Se compara
ademas con `B + QVoice`. `job_family_detail` queda fuera por su historia no
confiable.

## Diseno

- `F + QVoice`: C + `work_city` + la correccion QVoice seleccionada en CQ.
- `C + QVoice`: la version archivada de CQ, reajustada en cada origen con la
  misma seleccion QVoice.
- `B + QVoice`: variante `B_Q` archivada de la ronda V11.
- Ventanas: agosto-diciembre de 2025 y enero-febrero de 2026.
- Grupos: antiguedad x salidas del equipo x nivel; capacidad principal de 30%.
- `work_city`: categoria V11 construida con pais y ciudad registrados en la
  misma foto; las categorias se aprenden con el entrenamiento de cada corte.
- Modo `presentation`; no se guardan filas, identificadores ni predicciones
  individuales.

## Resultado

| Modelo | Log-loss x1000 (menor) | Brier x1000 (menor) | PR-AUC (mayor) | Lift 10% (mayor) | Captura 30% (mayor) | Error grupo-mes (menor) |
|---|---:|---:|---:|---:|---:|---:|
| C + ciudad + QVoice | 136.4 | 30.6 | 5.9% | 2.2 | 43.1% | 0.9 pp |
| C + QVoice | 137.7 | 30.7 | 5.5% | 2.1 | 43.1% | 1.0 pp |
| B + QVoice | 137.4 | 30.6 | 5.4% | 2.0 | 41.6% | 0.6 pp |

Frente a C + QVoice, `work_city` reduce el log-loss en 1.3 por mil, reduce el
Brier en 0.1 por mil, aumenta PR-AUC en 0.4 puntos porcentuales, aumenta el
lift en 0.1 y reduce el error de grupo en 0.1 pp. La captura al 30% cambia
menos de 0.1 pp.

Frente a B + QVoice, F + QVoice reduce el log-loss en 1.0 por mil y el Brier
en 0.04 por mil, aumenta PR-AUC en 0.5 pp, lift en 0.2 y captura en 1.5 pp.
El coste es un error de grupo 0.3 pp mayor. Por tanto, F + QVoice es un
challenger favorable para ranking y captura, mientras B + QVoice conserva la
mejor precision agregada de los grupos.

## Limites

La mejora de ciudad es consistente en los dos cortes para perdidas y error de
grupo; la captura solo cambia en el primer corte y permanece igual en el
segundo. La prueba no reoptimiza los grupos, no demuestra causalidad y solo
cubre las dos ventanas con QVoice. La decision vigente CQ permanece sin
cambios.

## Comprobación retrospectiva de agregados del candidato

La auditoría v1 comprobó 25 condiciones sobre los resultados guardados de la
corrida completa y una ejecución rápida de réplica. Comparó identificadores
de cortes, selección QVoice registrada, listas de predictores, ausencia de
`job_family_detail` en esas listas, concordancia de métricas y su dirección
por periodo. Pasaron 24 de 25 comprobaciones. Esta auditoría no reconstruyó
las personas del análisis, no calculó nuevos intervalos ni realizó otra prueba
fuera de muestra. El título histórico «validación formal» no debe interpretarse
como validación completa para uso por RH.

F + QVoice mejora log-loss, Brier, PR-AUC, lift y error de grupo en ambos
cortes. La única condición que no pasa es la regla histórica estricta que
exige una captura mayor en los dos periodos: F gana 0.1 pp en
agosto-diciembre de 2025 y empata en enero-febrero de 2026. La captura media
sí mejora 0.04 pp.

La conclusión es que F + QVoice se registra como **nuevo candidato
experimental** por mejorar las pérdidas, el ranking y el error de grupo en
ambos cortes, manteniendo o mejorando la captura. Esto se limita a las seis
métricas agregadas comparadas frente a CQ. CQ conserva su elección previa;
esa elección ya había considerado una victoria y un empate en captura, por lo
que la condición histórica estricta no impide por sí sola considerar FQ.
La [revisión de Julia y Brian](revision-julia-brian-salida-rh-20261012.md)
precisa las pruebas pendientes de calibración, cobertura por grupo, estabilidad
y utilidad para RH.

## Artefactos

- [Resultados](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-fast-v1/results.json)
- [Informe](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-fast-v1/informe.md)
- [Manifest](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-fast-v1/manifest.json)
- [Configuracion ejecutable](../../config/engineering_f_qvoice_comparison_20261013_fast.json)
- [Validacion formal](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-v3/validacion-f-qvoice.md)
- [Evidencia de validacion](../../output/analysis/engineering/20261013/model-f-qvoice-comparison-v3/validation-f-qvoice.json)
