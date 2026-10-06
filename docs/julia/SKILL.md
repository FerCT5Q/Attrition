---
name: morgan-vis
description: Create clear, explanatory data visualizations by clarifying the message, selecting a fitting chart, simplifying the design, amplifying the takeaway, and critically reviewing the result. Use for analytical charts, executive presentations, dashboards, reports, and data-storytelling workflows.
---

# Data Visualization Storytelling Skill

## Purpose

Create visualizations that help a specific audience understand an insight and decide or act. Optimize for clarity, honesty, interpretability, and consistency—not decoration or chart novelty.

Use AI as a thinking partner and reviewer, never as an unquestioned substitute for analytical judgment or chart construction.

## Core principle

> One chart, one message.

Every chart must communicate one clear takeaway. If there are multiple findings, decide whether they form a vertical story (each finding drills deeper into the previous one) or a horizontal story (related findings that do not contain one another), then use multiple coordinated charts when appropriate.

## The four-step framework

Always work through these steps in order:

1. **Clarify the message**
2. **Choose the chart**
3. **Simplify the visual**
4. **Amplify the message**

Do not start by choosing a chart type. Start with the insight.

---

## Step 1: Clarify the message

Transform a finding into a specific, audience-relevant insight.

### Investigate the number that first attracted attention

Use three angles:

- **Concentration:** Where is the pattern strongest? Break the overall result down by meaningful dimensions such as team, location, level, role, tenure, product, or segment.
- **Comparison:** Compared with what? Use another group, a benchmark, a target, a prior period, or an expected value.
- **Change:** How has the result moved over time? Distinguish sudden shifts from gradual changes.

A useful distinction:

- “The overall value is 72%” is a **finding**.
- “The value fell to 72%, primarily among senior employees, and is now below the company benchmark” is a **message**.

### Test whether the insight is actionable

Ask:

- Who is affected?
- What changed?
- Compared with what?
- Why might the audience care?
- What decision, investigation, or action could this support?

### Be precise about evidence

Do not convert association into causality. Use language that matches the data:

- Prefer: “is concentrated among,” “is associated with,” “coincides with,” “is the dominant theme among,” “may be contributing to.”
- Avoid unsupported claims such as “caused,” “drove,” or “resulted in.”

State important limitations, such as missing historical driver data, small samples, incomplete coverage, or the difference between current dissatisfaction and change over time.

### Decide what deserves visualization

Before creating a chart, consider whether the insight is better expressed as:

- **A large number:** when one value is the entire message and trend or comparison context is unnecessary.
- **A chart:** when the audience needs to see a trend, comparison, distribution, or relationship.
- **A table:** as supporting detail, exact values, or an accessibility companion—not usually as the primary storytelling device.

---

## Step 2: Choose the chart

Match the chart to the message and the audience.

### Trend over time

Use a line chart when the audience needs to understand movement across enough time points.

Rules:

- Represent time intervals honestly; equal gaps must represent equal amounts of time.
- Leave gaps for missing periods. Never connect missing data as if the value were known.
- Do not smooth lines by default; smoothing can imply changes that were not observed.
- Highlight the key series and mute contextual series when there are many lines.
- With only a few periods, consider bars if side-by-side comparison is more important than trajectory.

### Comparison across categories

Use bar charts when the audience needs to compare magnitudes.

- Use **vertical bars** for a small number of categories, short labels, or naturally ordered categories.
- Use **horizontal bars** for long labels or many categories.
- Sort categories logically when no natural order exists.
- Start bar-chart axes at zero. Cropped bar axes distort perceived magnitude.
- Avoid diagonal labels and unnecessary category density.

### Part-to-whole

Use a stacked bar when both the total and the composition matter.

- Decide whether the message is about raw magnitude or percentage composition.
- Include the full total, or clearly explain what is grouped or excluded.
- Limit the number of subcategories; consolidate minor categories into “Other” with a note.
- Remember that only segments sharing a baseline are easy to compare. Use panels or another chart if middle segments must be compared precisely.

Use a pie chart only when:

- The focus is one proportion of a whole rather than comparing many categories.
- There are few slices—ideally five or fewer, with six or seven as an upper limit.
- The key slice is anchored at 12 o’clock when practical.
- There are no 3D or exploded effects.

### Chart-selection workflow with AI

Do not ask AI to choose a chart before doing any thinking.

1. Create two or three rough mock-ups yourself.
2. State the insight and audience.
3. Ask AI to compare the mock-ups, explain its reasoning, identify trade-offs, and flag possible misinterpretations.
4. Decide which recommendation to accept.

---

## Step 3: Simplify the visual

Treat every default element as optional. An element earns its place only if it helps the audience understand the message.

### Remove clutter

Usually remove or reduce:

- Decorative borders, shadows, gradients, and 3D effects.
- Redundant chart titles and axis titles.
- Heavy gridlines; remove them when labels or a light reference structure are sufficient.
- Excessive tick marks and repeated date labels.
- Legends when direct labeling is feasible.
- Unnecessary colors and competing visual emphasis.

Use a reasonable axis range for line charts:

- Zoom in enough to reveal meaningful movement.
- Do not zoom so aggressively that small differences look dramatic.
- Do not zoom out so far that the pattern disappears.
- Leave modest breathing room around the data where appropriate.

### Direct labeling

Bring labels to the data instead of forcing the audience to move between a legend and the chart.

- Label lines or segments directly when possible.
- Label only the values that matter to the message—often the latest value, start and end values, maximum, minimum, or an important outlier.
- Label every value only when precision is central and the chart has enough space.

### Use color intentionally

Color is for emphasis, not decoration.

- Use one spotlight color for the key series or category.
- Use gray or a muted tone for context.
- Prefer one or two key colors per chart unless the message genuinely requires more.
- Keep color meaning consistent across charts in the same story.
- Do not rely on red/green alone; consider blue/orange, blue/yellow, line styles, labels, or markers for accessibility.
- Check whether cultural or organizational conventions change the meaning of a color.

---

## Step 4: Amplify the message

A clean chart still requires interpretation. Make the takeaway easy to find, even when the chart is forwarded without context.

### Write an active title

The title should state the takeaway, not merely describe the data.

Prefer:

- “Senior employees are driving the decline in engagement”
- “Revenue grew each quarter, reaching a record high in Q4”

Avoid:

- “Engagement by employee level”
- “Revenue by quarter”

Title rules:

- Lead with the conclusion.
- Use active, specific verbs such as grew, dropped, overtook, stalled, or recovered.
- Keep it to one line when possible, two at most.
- Add a descriptive subtitle only when the audience needs the measure, survey item, population, or unit of analysis.

### Add useful context

Use only context that strengthens the message:

- **Target or goal line:** shows whether performance meets an explicit goal.
- **Internal benchmark:** compares a group with an organization-wide or portfolio average.
- **External benchmark:** compares with an industry, competitor, or published reference. Cite the source.
- **Reference range:** shows an expected, acceptable, or historical high-low band.

Do not add multiple reference lines merely because they are available. Context should reduce interpretation effort, not create clutter.

### Use annotations to answer likely questions

Add a concise annotation when it helps explain:

- **Why:** a possible explanation for a notable shift.
- **What happened:** a launch, policy change, staffing event, market event, holiday, or methodology change.
- **What is unusual:** an outlier, missing period, break in methodology, or other feature that could be misread.

Use wording that distinguishes observed timing from proven causality. For example, “New promotion criteria introduced” is safer than “New promotion criteria caused the decline” unless causal evidence exists.

---

## AI collaboration protocol

### Use AI as a junior analyst for exploration

Provide context, not just a file:

- Your role and analytical objective.
- The audience and what they care about.
- The data structure and definitions, ideally with a data dictionary.
- The task.
- The desired deliverable and constraints.

Ask for **angles, not answers**. Request:

- Top patterns.
- Why each pattern may matter.
- Multiple hypotheses.
- Evidence supporting and weakening each hypothesis.
- Alternative explanations.
- Additional data that would strengthen the conclusion.
- Caveats and limitations.

Then pressure-test your working insight. Ask AI to try to disprove it, identify overstatements, and recommend more defensible wording.

### Use AI as a chart reviewer

After building the chart in the charting tool, provide the chart image or specification and ask AI to review:

- Whether the intended insight is obvious.
- Whether the chart type fits the message.
- Whether any design choice could mislead.
- Whether there is clutter or redundant information.
- Whether labels, colors, scales, and annotations work.
- Whether accessibility risks exist.
- What trade-offs each suggested change creates.

Require a rationale for every recommendation. Review the feedback critically; do not apply suggestions automatically.

### Do not delegate blindly

- Build the final chart directly in the charting tool when possible.
- Treat AI-generated numbers, patterns, and chart suggestions as unverified.
- Validate calculations against the source data.
- Do not allow AI to invent missing values, sources, or causal explanations.
- Ask AI to respond inline when file or chart generation is not requested.

---

## Multi-chart narrative

When a story requires multiple charts:

- Keep colors, fonts, title placement, source notes, and formatting consistent.
- Preserve the same visual meaning for spotlight and muted colors.
- Use comparable axis ranges for parallel findings when appropriate.
- Avoid switching chart types just to create variety.
- Pair tightly related charts on the same slide when the second only makes sense in the context of the first.
- Structure vertical stories as a progression from broad pattern to more specific explanation.

The audience should feel guided through one story, not presented with unrelated charts.

---

## Required quality-control checklist

Before delivering a visualization, verify:

### Message
- [ ] Can the takeaway be stated in one sentence?
- [ ] Is the message specific about who, what, compared with what, or over what time?
- [ ] Does the wording match the evidence and avoid unsupported causality?
- [ ] Are limitations and missing data acknowledged where relevant?

### Chart choice
- [ ] Does the chart type match the insight?
- [ ] Is one chart communicating one message?
- [ ] Are time intervals, missing data, and category order represented honestly?
- [ ] Does a text treatment or table make more sense than a chart?

### Design
- [ ] Does every visible element serve a purpose?
- [ ] Are unnecessary defaults removed?
- [ ] Are key values labeled without creating noise?
- [ ] Is color used to create a clear focal point?
- [ ] Is the visualization readable for people with color-vision deficiencies?
- [ ] Are bar axes anchored at zero?
- [ ] Is the line-chart range informative without exaggeration?

### Interpretation
- [ ] Does the title state the takeaway in active language?
- [ ] Is the most useful benchmark or reference range included and labeled?
- [ ] Do annotations answer likely questions without overstating certainty?
- [ ] Can the chart stand alone if it is forwarded without its original context?

### Review
- [ ] Were the numbers checked against the source data?
- [ ] Were rough chart alternatives considered where the choice was ambiguous?
- [ ] Was AI used to challenge the work rather than replace judgment?
- [ ] Were trade-offs reviewed before changes were accepted?

---

## Recommended response format when creating a visualization

When asked to create or improve a chart, produce or document the work in this order:

1. **Audience and decision:** who will use it and what decision or action it supports.
2. **Core message:** one-sentence takeaway.
3. **Evidence and caveats:** key values, comparison, trend, sample, and limitations.
4. **Chart choice:** selected chart and why alternatives were rejected.
5. **Design specification:** title, subtitle, axes, labels, colors, annotations, benchmark, and accessibility choices.
6. **Validation:** checks performed against the source data.
7. **Final review:** remaining trade-offs or interpretive risks.

## Example AI prompts

### Explore a dataset

```text
Act as a careful junior analyst. Do not create charts or files. First, read the data dictionary and explain any ambiguities.

Context:
- My role: [role]
- Audience: [audience]
- Business question: [question]
- Data: [description and time period]

Find:
1. The strongest patterns related to the business question.
2. Where each pattern is concentrated.
3. Meaningful comparisons and changes over time.
4. Multiple hypotheses, ranked by strength of evidence.
5. Alternative explanations and important caveats.
6. Additional data that would strengthen or challenge the conclusions.

Show the calculations behind important claims. Do not infer causality from association or timing alone.
```

### Pressure-test an insight

```text
Pressure-test this proposed insight against the attached data:

Proposed insight: [one sentence]

Try to disprove it. Identify:
- Claims supported by the data.
- Claims that are too strong or too broad.
- Alternative explanations.
- Missing data or sample limitations.
- More defensible wording.

Show the evidence and rationale. Do not simply confirm the conclusion.
```

### Compare chart mock-ups

```text
I created the attached chart mock-ups for this insight:
[insight]

Audience: [audience]
Decision or action: [decision]

Compare the mock-ups and recommend the best fit. Evaluate:
- Alignment between chart type and message.
- Speed of comprehension.
- Risk of misleading interpretation.
- Accessibility and labeling.
- Clutter and unnecessary complexity.

Explain the rationale for every recommendation and list the trade-offs. Do not generate a replacement chart.
```

### Critique a finished chart

```text
Review the attached chart as a critical second set of eyes.

Intended insight: [one sentence]
Audience: [audience]

Assess:
- Is the takeaway obvious within a few seconds?
- Does the chart type fit the message?
- Are scales and time intervals honest?
- Are labels, colors, annotations, and benchmarks useful?
- What could be removed?
- What accessibility risks exist?
- Could any element imply unsupported causality or exaggerate the pattern?

For each suggestion, provide the rationale and trade-offs. Do not assume your recommendation is automatically correct.
```
