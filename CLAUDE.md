# CLAUDE.md

Las reglas obligatorias del proyecto están en `AGENTS.md` y se aplican
íntegramente:

@AGENTS.md

## Qué es este proyecto

Evaluación y documentación de variables candidatas para un modelo de
attrition voluntaria a seis meses (cohortes, no scores individuales). Cada
variable se evalúa en ocho criterios (`Source`, `Definition`, `Coverage`,
`Missingness`, `Consistency`, `History`, `Join`, `Effort`) con evidencia
agregada de Redshift (`hrda`). Contexto: `docs/context/model-overview.md` y
`docs/context/assessment-methodology.md`. No es un repositorio git.

## Skills del proyecto (no se cargan automáticamente en Claude Code)

Los skills que exige `AGENTS.md` viven en `.codex/skills/` (formato Codex), así
que no aparecen en la lista de skills de Claude Code. Antes de cualquier
consulta a Redshift o evaluación de variable, **lee el `SKILL.md` completo y
las referencias que indique**:

- `.codex/skills/attrition-redshift-db/SKILL.md`: consultas read-only,
  modos `presentation` / `internal_analysis`, `references/schema.md` y
  `references/reporting-modes.md`.
- `.codex/skills/evaluate-attrition-variable/SKILL.md`: flujo v4,
  `references/scoring-rules.yaml` (fuente de verdad de umbrales y scores),
  `assessment-spec.md`, `semantic-validation.md`, `semantic-hints.yaml`,
  `workflow-contracts.md`.
- `.codex/skills/explora-esquema-hrda/SKILL.md`: exploración del esquema.

Skills de visualización y presentaciones: la copia canónica está en
`.agents/skills/` (Codex). `.claude/skills/morgan-vis` y
`.claude/skills/build-html-presentation` son junctions de Windows hacia esa
carpeta; edita en cualquiera de las dos rutas (es el mismo archivo) y nunca
borres el contenido de una junction.

- `morgan-vis`: metodología de Julia (mensaje, gráfico, simplificar,
  amplificar, autocrítica). El original intacto está en `docs/julia/SKILL.md`.
- `build-html-presentation`: decks HTML que combinan `morgan-vis` con la
  plantilla de `html-slide-generator` (instalado en `~/.codex/skills/`).
  Incluye `scripts/verify_deck.py`.

El comando `/db` (`.claude/commands/db.md`) usa `SqlService` del proyecto
Slides y no aplica los guardarraíles de este proyecto. Para Attrition usa el
helper del skill `attrition-redshift-db`.

## Entorno y comandos

- Python: `.venv\Scripts\python.exe` (dependencias en `requirements.txt`).
  Ejecuta scripts con `-B`.
- Credenciales: se reutilizan desde `C:\Dev\Python\Slides\.env`. No las copies
  a este proyecto.
- Consulta ad hoc read-only:
  `.venv\Scripts\python.exe -B .codex\skills\attrition-redshift-db\scripts\run_readonly_query.py --sql "<query>" --max-rows 100`
  (añade `--reporting-mode internal_analysis` sólo si el usuario lo pidió de
  forma explícita).
- Runner v4: `.codex\skills\evaluate-attrition-variable\scripts\run_assessment.py`
  con `--request <run-request.yaml> --preflight-only` y después
  `--strict-analysis-plans --analysis-plan ...`. Carga por defecto
  `config/variable_assessment_project.yaml`.
- Pruebas (unittest):
  - Proyecto: `.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py"`
  - Skill: `.venv\Scripts\python.exe -B -m unittest discover -s .codex\skills\evaluate-attrition-variable\tests`
- Vista navegable de resultados:
  `.venv\Scripts\python.exe tools\generate_current_output.py` (`--verify` para
  validarla sin modificarla).

## Convenciones de archivos

- Specs, planes y requests en `config/` son versionados e inmutables: crea
  `..._plan_vN+1_<YYYYMMDD>.yaml` en lugar de editar uno ya ejecutado.
- SQL con fecha en el nombre: `queries/audits/<concepto>_<chequeo>_<YYYYMMDD>.sql`.
- Evidencia por concepto: `tools/build_<concepto>_evidence.py` con su prueba
  en `tests/test_<concepto>_*.py`.
- `output/assessments/<run-id>/` es inmutable. `output/current/` se genera
  con enlaces; no edites lo que apunta.
- `output/distribution/` contiene los decks de distribuciones (versión vigente
  v8, política de colores en `config/attrition_color_policy_v8.json`).
- Hay capturas `.png` sueltas en la raíz de sesiones anteriores. No añadas
  más: van a `tmp/` o `output/preview/`.
