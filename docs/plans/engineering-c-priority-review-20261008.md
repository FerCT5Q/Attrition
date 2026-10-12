# Revisión de los grupos prioritarios de C

8-oct-2026. Modo `presentation`. Solicitada al elegir «Grupos de C» como
siguiente paso. Se usa `morgan-vis` para el informe y la figura.

## Preguntas y método

1. ¿Qué grupos entran en la prioridad del 30% y cuánto cambia la cobertura
   si se actúa sobre grupos completos? Leer `C_Bcuts` de la extensión del
   22-feb-2026, seguida hasta 22-ago-2026. Mantener las capacidades archivadas.
2. ¿Cuáles concentran riesgo y cuáles están mal estimados? Mostrar riesgo
   acumulado a seis meses estimado y observado, tamaño, error con signo y
   referencia de toda la población. Mantener las supresiones del origen.
3. ¿La presencia en prioridad es persistente? Contar las fotos seleccionadas
   de cada uno de esos grupos en los cuatro periodos históricos de seis
   snapshots; cero significa ausencia de prioridad, no riesgo bajo probado.
4. ¿Qué acciones merece la pena explorar? Separar la señal observada de la
   hipótesis de carrera, carga o continuidad. No atribuir causas ni estimar
   salidas evitables; proponer diagnóstico y medición de un eventual piloto.

## Alcance

Datos agregados ya publicados: `c-group-selection-v1/results.json`, variante
`C_Bcuts`; coeficientes archivados de C con origen 1-ago-2025. Población:
Engineering, Employee, Regular, activo, sin RF360. C sigue sin QVoice.

La última foto madura archivada no es una asignación actual de personas.
Los grupos son antigüedad × salidas previas del equipo × nivel. Nivel de
entrada/medio/alto describe nivel profesional, sin inferir edad.

La capacidad exacta usa pesos uniformes en el grupo del límite. Para los
nueve grupos de la prioridad del 30%, el escenario del 40% contiene sus
tamaños completos. Se exige que sus conteos sean enteros y que, cuando el
observado es publicable, reconcilien con los eventos distintos y la tasa.
No se reconstruyen observados suprimidos. La referencia poblacional se
obtiene como observado en prioridad / lift y se reconcilia entre capacidades.

## Entregables y controles

Nueva carpeta `model-c-priority-groups-v1`: informe, tabla CSV, agregados JSON,
figura PNG/SVG, configuración y fuentes congeladas, comprobaciones y manifest.
Comprobar sumas de tamaños y predicciones, capacidad, límites temporales,
preservación de supresiones y hashes de los artefactos anteriores. No hay
consultas, reentrenamientos ni tests de software. No se asignan scores.
