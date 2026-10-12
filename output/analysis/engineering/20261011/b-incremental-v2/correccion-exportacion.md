# Corrección antes de repetir el experimento

Modo `presentation`. No contiene filas ni predicciones de empleados.

La v1 se detuvo en el segundo periodo por su comprobación de reproducción
del modelo guardado. El ajuste usaba las columnas en orden del catálogo;
al exportarlo, la lista de variables conservaba el orden de selección.
Cuando esos órdenes diferían, el encoder reconstruía una matriz distinta.

Se corrigió la alineación en los contextos de RH y QVoice. El orden de las
columnas y coeficientes determina ahora también el orden de variables del
encoder exportado. No se cambió la selección estadística ni se alteraron
los modelos B, C y CQ anteriores a este experimento.

Dos pruebas de regresión usan combinaciones de tres variables en orden
distinto del catálogo, con datos exclusivamente sintéticos. Antes de la
corrección ambas fallaron; después ambas pasan. La prueba RH comprueba
también equivalencia con un ajuste directo independiente del contexto.

La ejecución v1, sus resultados parciales y sus fuentes originales se
conservan en `../b-incremental-v1/`. La v2 repite el cálculo completo.
