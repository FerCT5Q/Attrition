# Reproducción del análisis

Modo `presentation`. El resultado contiene sólo parámetros y agregados. Las
filas de entrenamiento y evaluación se vuelven a cargar en RAM bajo la
autorización de 1-oct-2026; no existe caché individual. Una modificación
retroactiva de Redshift puede cambiar los resultados: reconciliar primero
población, eventos y referencia CQ contra la ejecución archivada.

1. Copiar `config/julia_rh_review_20261012.json` a otro archivo dentro de
   `config/`, con un `run_id` y una carpeta `output` nuevos. Conservar fechas,
   población, variables, L2, capacidades y reglas de la comparación.
2. Preparar la documentación antes del cálculo:
   `.venv/Scripts/python.exe -B tools/build_julia_review_documents.py --output <carpeta-nueva>`.
3. Ejecutar el bloque compartido:
   `.venv/Scripts/python.exe -B tools/engineering_julia_rh_review.py --config <config-nueva>`.
   El script rechaza sobrescribir una corrida con `results.json`.
4. Completar los cruces con los seis modelos guardados, sin ajustes:
   `.venv/Scripts/python.exe -B tools/complete_julia_cohort_diagnostics.py --config <config-nueva>`.
5. Aplicar la supresión de márgenes de ventana antes de publicar:
   `.venv/Scripts/python.exe -B tools/verify_julia_review_delivery.py --guard --output <carpeta-nueva>`.
6. Generar el informe y Excel desde los agregados:
   `.venv/Scripts/python.exe -B tools/render_julia_rh_review.py --output <carpeta-nueva>`.
7. Crear una copia nueva del deck, con base explícita:
   `.venv/Scripts/python.exe -B tools/presentations/build_julia_rh_review_deck.py --run <carpeta-nueva> --output <carpeta-deck-nueva> --base <html-base>`.
8. Verificar artefactos:
   `.venv/Scripts/python.exe -B tools/verify_julia_review_delivery.py --output <carpeta-nueva> --deck <html-nuevo>`.
   Las aserciones de resultados del verificador corresponden a esta revisión;
   una diferencia exige explicación, no cambiar umbrales para hacerla pasar.
9. Ejecutar las siete pruebas numéricas/sintéticas de
   `tests/test_julia_review_statistics.py`. Revisar el deck en navegador a
   1440×810 en sus cuatro temas; el script usado está en
   `tools/presentations/verify_julia_review_browser.js`.

El escalar R6 es un contraste retrospectivo. Se activa por sesgo e intervalo
del periodo evaluado, pero se ajusta con predicciones de orígenes anteriores
y maduros. La elección de variables y penalizaciones queda condicionada a
las selecciones archivadas, sin nueva búsqueda anidada en los auxiliares.

Los scripts iniciales de cálculo están en `source/`; las revisiones
documentales posteriores, cuando difieren, en `source-final/`. Las versiones
de librerías se registran en `environment.json`. Los modelos y covarianzas se
guardan por periodo. Las nueve bases y nueve correcciones auxiliares están
identificadas con prefijo `aux-`; no son nuevos candidatos seleccionados.

El finalizador de esta entrega usa las rutas de su propia ejecución; para
otra revisión, registrar un nuevo manifest con sus hashes y pruebas. No
modificar el registro del modelo elegido sin una decisión explícita.
