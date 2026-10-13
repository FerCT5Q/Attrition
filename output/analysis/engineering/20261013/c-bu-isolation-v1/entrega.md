# Cierre de la ampliación C + BU y del deck

Modo `presentation`. La comparación terminó con cuatro ajustes RH y dos
correcciones QVoice. CQ, FQ y FQ + BU archivados fueron reproducidos; las
siete pruebas estadísticas pasaron. `verification.json` conserva los
controles de población, capacidad, serialización, fechas y exclusiones.

La [interpretación para Julia](../../../../../docs/context/c-bu-isolation-20261013.md)
separa mejoras de pérdidas, captura y error. C + BU sin QVoice no supera el
balance de CQ; añadir encuesta y ciudad aporta mejoras de estimación. El
modelo elegido sigue siendo CQ.

La [presentación corregida](../../../../presentations/20261013-0735_revision-julia-9-slides/presentacion-eng.html)
mantiene nueve slides de la base original, el orden, inglés y diseño útil.
Conserva las animaciones originales y actualiza resultados y lectura RH.
70 comprobaciones de entrega pasaron, junto con revisión de 36 capturas,
navegación, cuatro temas, animaciones y enlaces. La única excepción al
verificador estático genérico es el inglés requerido por AGENTS.md.

La [guía ampliada de 44 variables](documentacion/variables-44-ampliada.xlsx)
conserva el inventario y añade 176 filas de uso: dos modelos por dos cortes
por 44 variables. Codificaciones extraídas de los artefactos guardados;
ningún nuevo score de assessment. Regeneración:
`tools/extend_julia_variable_guide_c_bu.py`.

La reproducción del deck usa
`tools/presentations/revise_julia_review_nine_slides.py`; su validación usa
`tools/presentations/verify_julia_nine_delivery.py` y
`tools/presentations/verify_julia_nine_browser.js`.
