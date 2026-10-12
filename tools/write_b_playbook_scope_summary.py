"""Resumen legible del alcance congelado, sin leer datos de empleados."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
config = json.loads((ROOT/'config/engineering_b_playbook_v11_20261012.json').read_text(encoding='utf-8'))
scope = json.loads((ROOT/config['playbook_scope']).read_text(encoding='utf-8'))
lines = ['# Alcance de B + candidatas del playbook V11','',
         'Modo `presentation`. Preparación congelada el 12-oct-2026. Este documento describe el alcance; las mejoras predictivas se publican en el informe de resultados.','',
         'Se conservan los ocho predictores y las dos interacciones de B. Se prepararon 41 candidatas RH y 51 QVoice. Las preguntas comunes de QVoice se prueban individualmente y los aliases no se cuentan dos veces.','',
         'La referencia es `'+scope['source']+'`, SHA256 `'+scope['source_sha256']+'`.','',
         'El nombre «43 variables» identifica el playbook. Su revisión actual tiene 42 vistas analíticas; varias contienen preguntas, cruces o representaciones distintas de un concepto. Por ello el total de candidatas no es el número de vistas.','',
         '| Slide | Vista | Prioritaria | Preparación | Candidatas o términos de B | Alcance y limitación |',
         '|---:|---|---|---|---|---|']
for row in scope['views']:
    labels = ', '.join(config['feature_labels'].get(f,f) for f in row['representaciones']) or '—'
    lines.append(f'| {row["slide"]} | {row["vista"]} | {"Sí" if row["prioritaria"] else "No"} | {row["estado"]} | {labels} | {row["explicacion"]} |')
lines += ['', 'Preparada significa que existe una representación reproducible; cada corte todavía exige historia suficiente. No seleccionable describe una brecha de datos, no falta de utilidad predictiva. No se cambian scores de assessment.','',
          'Los periodos externos, controles y comparaciones finales se guardan en `informe.md`, `comparacion-variables.csv` y `results.json` de esta misma carpeta al terminar la ejecución.','']
(ROOT/config['output']/'alcance-v11.md').write_text('\n'.join(lines),encoding='utf-8')
print('Alcance V11 legible guardado: 42 vistas, 41 candidatas RH y 51 QVoice.')
