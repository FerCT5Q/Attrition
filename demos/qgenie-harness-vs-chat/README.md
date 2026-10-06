# QGenie Chat vs. Harness: demo project

This is a small, independent demonstration for an AI meeting. It is not part
of the Attrition project and does not use personnel data.

## Story

A project manager receives a status spreadsheet and meeting notes. Leadership
needs a concise status report, a list of risks, and an action tracker.

The source files contain one deliberate disagreement: the spreadsheet keeps an
old planned date for the billing integration, while the meeting notes mention
a revised expectation. The agent should surface the conflict instead of
silently choosing one value.

## Folder layout

```text
demo-harness-vs-chat/
|-- AGENTS.md
|-- input/
|   |-- meeting_notes.md
|   |-- project_rules.md
|   |-- project_status.csv
|   `-- report_template.md
|-- output/
`-- prompts/
    |-- chat.md
    |-- harness_execute.md
    `-- harness_plan.md
```

Keep `output/` empty at the start of the demonstration.

## Presentation flow

### Part 1: QGenie Chat

Upload the files from `input/` or place them in a QGenie Chat Content Group.
Use the prompt in `prompts/chat.md`.

Point out that Chat can analyze, summarize, and rewrite the information very
well. The result remains primarily inside the conversation. The presenter
still needs to transfer it to the project folder or another document.

### Part 2: Harness

Open this folder as the working directory for Codex, Claude Code, or another
configured harness. Use `prompts/harness_plan.md` first. The agent should read
the project context and present a plan without changing files.

After showing the plan, approve it with the prompt in
`prompts/harness_execute.md`.

Show the audience that the agent:

1. Inspected the local project.
2. Used the project instructions and source files.
3. Validated the dates and statuses.
4. Detected the conflicting billing date.
5. Created deliverables under `output/`.
6. Left the source files untouched.

Open the generated report in a browser or editor. The visible difference is
that the harness did not just describe a report: it created one in the working
environment.

## Suggested narration

Before the Chat demo:

> En el Chat le voy a pedir a la IA que analice la informacion que le entrego.

Before the harness demo:

> Ahora no le voy a adjuntar cada archivo ni repetirle todas las reglas. El
> proyecto ya contiene el contexto de trabajo. Le voy a delegar una tarea.

After the harness creates the files:

> La diferencia no es solamente la respuesta. El agente pudo leer el proyecto,
> aplicar reglas, validar informacion y crear un resultado dentro de la carpeta.

## What is hidden from the audience

- `AGENTS.md` represents project-level instructions.
- A skill can provide the repeatable reporting procedure.
- An MCP can provide an authorized connection to a project tracker or document
  system. For this demo, local fixtures make the result reliable.
- The harness supplies the tools for reading, writing, running checks, and
  requesting approval.

The audience does not need to learn how to build any of these components. They
only need to describe the work they want completed.

## Safety and fallback

Use only this synthetic project in the live demonstration. Keep the harness in
plan-first or approval mode. If the live run is affected by network or model
availability, show a saved run of the same sequence and open the generated
files from `output/`.
