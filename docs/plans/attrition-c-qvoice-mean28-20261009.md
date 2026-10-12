# Evaluación retrospectiva de C + Q con promedio de 28 preguntas

Fecha: 9-oct-2026. Modo `presentation`. Etapa: selección de modelo.

## Solicitud y diferencia frente a la prueba anterior

El usuario pide evaluar C + Q + promedio y actualizar la tabla de selección.
Se interpreta como la variante final con promedio de 28 mencionada en la
conversación; se incluye la media de 33 como control explícito.

La revisión de solapamiento ya probó una política de selección de subconjuntos
con media. Esos subconjuntos cambiaron entre periodos. Aquí se prueba la
misma combinación concreta en ambos periodos:

`Career Goals + Q8 + Q10 + Q11 + Q13 + Q17 + media de 28`.

Se elige esta estructura porque es la solicitada y corresponde a la selección
de septiembre. **La definición del candidato se conoce tras explorar el
histórico**: este backtest es retrospectivo y condicionado a esa elección,
no una validación prospectiva ni independiente de toda la selección previa.
Los coeficientes y L2 sí se ajustarán usando únicamente el pasado de cada
origen. No se puntúan fotos pasadas con coeficientes aprendidos en septiembre.

## Población y calendario

Engineering, Employee, Regular, activo, sin RF360. Filas persona-snapshot sólo
en RAM bajo la autorización del 1-oct-2026. Grupos de al menos 300 personas;
tasas concretas publicables con 30 personas y 30 eventos distintos.

Conocimiento hasta 7-sep-2026. QVoice 2024 se usa en 2025 y 2025 en 2026,
con continuidad del episodio. Evaluación: agosto–diciembre 2025 y
enero–febrero 2026, cada foto seguida seis meses hasta agosto de 2026.
Media con igual peso por periodo; personas y seguimientos parcialmente
compartidos. Capacidad principal 30%, sensibilidades 20% y 40%.

## Variable derivada y comprobación

Tipo `derived_feature`, componentes `survey`: proporción de indicadores
favorables de 28 ítems. Numerador = suma de los restantes; denominador = 28.
Se excluyen del conjunto comparable de 33 las preguntas Q8, Q10, Q11, Q13 y
Q17, que ya entran por separado. Career no está entre los 33. Mapping por texto
canónico, congelado y reconciliado entre waves. Los componentes excluidos son
M09, M13, M29, M12 y M27. No son respuestas Likert.

Se mantienen las bandas `<50`, `50–69`, `70–79`, `80–89`, `90–99`, `100`.
La elegibilidad exige los 33 ítems válidos para ambas medias; los estados de
ausencia no se sustituyen por desfavorables. Aceptación: cero diferencias de
mapping, bandas, fórmula o elegibilidad en recálculo independiente. Sin
cambios en scores de assessment. La derivación y diagnósticos se terminan
antes de interpretar las métricas predictivas.

## Comparadores y método

1. C archivado.
2. C + Q archivado: procedimiento elegido provisionalmente en la conversación.
3. C + preguntas fijas + media de 33.
4. C + preguntas fijas + media de 28.
5. C + las mismas preguntas fijas, sin media.
6. Control de disponibilidad propio de la variante con media de 28.

Restaurar C/CQ sin reajustarlos. Reutilizar los intervalos internos anteriores
a cada origen del experimento original. Filtrar la búsqueda archivada al
subconjunto concreto con media; contrastar su Brier interno al reproducirlo.
Elegir L2 en {0.1, 1, 10} por representación y reajustar la corrección antes
de su ventana externa. No repetir los 780 candidatos originales.

La calibración posterior se conserva en identidad para comparar cambios de
representación. El artefacto final de septiembre con media de 28 ya existe y
se copiará de forma verificable; no requiere repetir su ajuste.

## Tabla y decisión

Grupos principales comunes: antigüedad × salidas del equipo × nivel.
Sensibilidad separada: añadir adquisición registrada. Comparar captura,
log-loss, Brier, PR-AUC, sesgo y error por grupo/grupo-mes. Medir también
probabilidades sobre exactamente la prioridad elegida por C. Intervalos
pareados con 500 remuestreos de personas, condicionales a modelos y prioridades.

La tabla conserva el resultado de la regla estricta anterior (ganar ambos
periodos), pero la elección en esta etapa no será un conteo de condiciones.
La referencia preferida es CQ por el balance ya discutido. Para favorecer
la variante con media se buscará una mejora de captura consistente o, con
captura equivalente, mejor precisión de grupos sin deterioro relevante de
pérdidas. Tolerancias heredadas: +0.1 pp en error de grupos, +0.5% relativo
en pérdidas. Reportar incertidumbre y magnitud; no elegir por una diferencia
interna diminuta. No implica piloto ni despliegue.

## Entrega

Carpeta independiente `output/analysis/engineering/20261009/c-qvoice-mean28-v1/`:
modelos por periodo, copia del final, tabla CSV/Markdown, informe y evidencia.
Consulta temporal copiada exactamente bajo nombre nuevo en `queries/profiles/`.
Usar cliente del skill `attrition-redshift-db`; aplicar reglas de derivación
de `evaluate-attrition-variable` y narrativa de `morgan-vis`. Se conservan
todos los modelos anteriores y se actualiza una nota contextual nueva de
selección con el resultado medido, sin reescribir informes históricos.
