# C: cruces de cuatro variables y agrupación de mayor detalle

8-oct-2026. Plan previo al cálculo. Modo `presentation`.

## Pregunta y alcance

El usuario plantea que una cuarta variable podría mejorar los grupos y que
unos 40 grupos podrían ser útiles. Hipótesis: dividir segmentos amplios con
señales adicionales ya incorporadas en C permitirá priorizar mejor grupos
con riesgo diferente, conservando reglas interpretables.

Se congela el hazard C. No se seleccionan de nuevo sus coeficientes ni se
incorpora QVoice. Cambian únicamente los cortes con los que se resumen y
ordenan sus riesgos. Las pérdidas globales individuales permanecen iguales.

Población: Engineering, Employee, Regular, activo, sin RF360. Outcome: salida
voluntaria en seis meses desde cada snapshot. Se reutiliza la consulta de C
`queries/profiles/engineering_model_c_person_month_20261008.sql` y su frontera
de conocimiento 7-sep-2026. Sólo RAM bajo la autorización existente; ningún
registro, llave o riesgo individual se guarda o publica.

Skills: `attrition-redshift-db` para la lectura autorizada y `morgan-vis` para
la explicación. Se reutilizan contratos y representaciones previas; no es un
assessment de variables, no se atribuyen significados nuevos ni se cambian scores.

## Variables y semántica de los cortes

Los tres cortes actuales permanecen exactos: antigüedad, salidas previas del
equipo y nivel agrupado. Son la referencia `C_current`.

Las dimensiones adicionales proceden sólo de los términos principales del C
archivado en cada origen. Se excluyen calendario e interacciones como
dimensiones, y no se repite un concepto con dos codificaciones en un cruce.
Se usan las bandas originales del modelo, manteniendo estados faltantes;
esto conserva más detalle que las versiones binarias de la búsqueda previa.

Conceptos posibles según el C de cada fecha: cambios de manager, reportes
directos, tiempo desde promoción, recontratación, experiencia previa, tiempo
en nivel, IOS, capas almacenadas, región, comp ratio en bandas, adquisición,
transferencias y los otros términos presentes en los C históricos. Sus
definiciones y limitaciones se heredan de C. No se afirma causalidad ni se
equipara coeficiente grande con importancia predictiva.

## Comparaciones declaradas

- `C_current`: cortes actuales de tres variables.
- `C_plus1` (principal): los tres cortes actuales más una variable.
- `C_four`: todos los cruces de cuatro conceptos admisibles.
- `C_near40`: cruces de cuatro conceptos con promedio de 30–50 grupos en
  desarrollo. El número exacto puede cambiar con la población de cada foto.

Cada grupo necesita 300 personas por foto. Un candidato de desarrollo debe
tener como máximo 50 grupos elegibles por foto y cubrir al menos 80% de la
población con grupos elegibles. Los grupos pequeños permanecen en resto.
Sólo se publican tasas con 30 personas por foto y 30 personas distintas con
evento; se mantienen las supresiones.

## Selección temporal

Restaurar cuatro C, cero reajustes. Para cada origen externo, seleccionar la
agrupación con las seis últimas fotos cuyo seguimiento R6 terminó antes del
origen. Evaluar después en seis fotos externas, reproduciendo los cuatro
periodos de C: febrero–julio 2024, agosto 2024–enero 2025, febrero–julio 2025
y agosto 2025–enero 2026. La foto de febrero 2026 se muestra como extensión
separada con la selección del último origen, sin convertirla en un quinto fold.

Las etiquetas de desarrollo participaron parcialmente en el entrenamiento de
C. Las salidas externas no escogen cortes. Son periodos retrospectivos ya
explorados; la evaluación no se presenta como una muestra externa nueva.

Seleccionar por captura al 30%, con tolerancia del 2% relativo del máximo.
Entre los candidatos cercanos, usar el menor exceso de error grupo-mes sobre
la prioridad actual evaluada con esa misma partición candidata, tolerancia
0.1 pp; después menor número de grupos, mayor captura y nombre estable.

Si una familia no tiene candidatos admisibles, usar los cortes actuales y
registrar el fallback. En evaluación, si los grupos elegibles no alcanzan
40% de la población, aplicar el mismo fallback sin usar resultados de salida.

## Métricas y criterio

Capacidades iguales de 20%, 30% principal y 40%; peso uniforme en grupo del
límite, con alternativas de grupos completos. Medir captura, riesgo estimado
y observado, error por grupo y grupo-mes, mayor error publicable, cobertura
publicable, número de grupos y resto.

Dividir grupos puede elevar el error al revelar heterogeneidad. Además del
error propio, calcular el error de ambas prioridades sobre los mismos
subgrupos candidatos. La regla principal compara esas dos prioridades con
idéntica granularidad, aunque sus personas priorizadas puedan diferir.

Promedio de cuatro periodos con igual peso. IC95 pareado mediante 500
remuestreos por persona, conservando todas sus ventanas. Evidencia favorable:
IC95 de captura medio positivo, al menos tres victorias de cuatro periodos,
error por grupo y grupo-mes no mayor al control comparable más 0.1 pp.
Reportar también cuántas definiciones distintas se eligen entre periodos.

Las familias secundarias y capacidades adicionales son diagnósticas;
intervalos puntuales sin ajuste por comparaciones múltiples. Una combinación
final distinta entre cortes evalúa una política de selección, no una regla
única probada en todos los periodos.

## Eficiencia y entregables

Cargar una sola vez el frame; precalcular riesgos y fechas por periodo.
Codificar cruces con índices enteros y acumular celdas en memoria, evitando
ordenar cadenas y repetir ajustes del modelo por candidato.

Nueva carpeta `output/analysis/engineering/20261008/c-fourway-groups-v1/`:
selecciones, métricas, cortes archivados, comparación, informe y figura.
Reproducir población, métricas C y cortes actuales contra los archivos
anteriores. Comprobar capacidades y cálculos, guardar hashes y conservar
intactos los modelos anteriores. No añadir ni ejecutar suites de software.
