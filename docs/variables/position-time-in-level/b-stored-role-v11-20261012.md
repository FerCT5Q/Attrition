# Tiempo en rol almacenado: representación V11 para B + X

Modo `presentation`. El V11 compara tiempo en perfil calculado desde fecha de
inicio y `time_in_role` almacenado. El perfil ya se preparó por separado; no
se supone que ambas medidas sean equivalentes ni que el segundo campo mida
tiempo en nivel. La fórmula y los resets oficiales de `time_in_role` siguen
pendientes de confirmar.

Antes de consultar: candidata `time_in_role_stored_v11`, tipo
`precomputed_metric`, para contrastar el aporte del valor almacenado. Se
conservan los cortes numéricos V11 1, 2, 3, 5 y 10, sin afirmar una unidad o
fórmula que no se haya reconciliado. Población: Engineering, Employee, Regular,
activo y sin RF360 entre 26-jul-2020 y 7-sep-2026; grain persona-foto mensual,
valor de la propia foto. Nulos y negativos quedan desconocidos.

Pregunta: ¿el dato tiene historia suficiente y se reproducen exactamente sus
bandas sin duplicados o valores contradictorios? Motivo: evitar confundir
falta de historia con cero y documentar su diferencia frente al tiempo desde
inicio del perfil. Método: auditoría anual del grain, cobertura, primer dato,
negativos y recálculo independiente de bandas mediante conteo de umbrales.
Regla previa: cero duplicados, contradicciones o diferencias de codificación;
los negativos no pueden quedar observados. La historia mínima de selección
es la del protocolo (seis fotos observables en entrenamiento), no se relaja.
Una verificación de bandas no confirma la fórmula de origen ni habilita un
score de definición 2. No se cambian scores.

## Resultado al 12-oct-2026

La auditoría `queries/audits/engineering_b_v11_stored_role_20261012.sql`
pasó para los siete años. Su JSON
`output/analysis/engineering/20261011/b-playbook-v11-v1/input-evidence/v11-stored-role.json`
conserva fecha, SQL y hashes. Hubo cero duplicados, contradicciones, negativos,
bandas distintas o inválidos tratados como observados. No hay valores antes
de **24-ago-2025**; se observan 168,175 persona-fotos en cinco cierres de 2025
y 288,586 en ocho cierres de 2026.

Conclusión: se incluye `time_in_role_stored_v11` como representación del valor
almacenado. La carga usa
`queries/profiles/engineering_b_v11_stored_role_person_month_20261012.sql`.
Su historia corta puede impedir seleccionarla aunque la codificación sea
correcta; el requisito de seis fotos se comprobará dentro de cada corte.
La correspondencia con V11 explicará esta restricción y la diferencia frente
al perfil calculado. La fórmula/unidad de origen y sus resets siguen sin
confirmación; esta prueba no cambia el score histórico.
