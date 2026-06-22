# HARP Tech-Share Writing Template

This is the direct writing scaffold extracted from `harp_tech_share.html`. Use it when the user asks for a deck, HTML report, architecture truth source, postmortem, or project explainer in the same style.

The template is intentionally fill-in oriented. Replace bracketed placeholders with the project-specific story, evidence, paths, figures, and honest limits.

## Deck-Level Template

```text
Title:
  Eyebrow: [Tech Share / Architecture Review / Postmortem] · [date]
  H1: [System name]: a [control plane / harness / runtime / substrate] for [bounded long-loop work]
  Subtitle: How [system] turns [messy human/agent workflow] into [bounded, auditable, reviewable loop].
  Pills: [cron-driven] [agent-backed] [git-audited] [skill-extensible] [benchmark-aware]

1. Warm-up / history
  Claim: [System] did not appear in isolation; it is the answer to [historical pressure].
  Visual: 4-6 stage strip from manual work to harnessed long-loop work.
  Thesis: My judgment: [realistic medium-term thesis], not [overclaim].

2. Short-step breakthrough
  Claim: The primitive that recently became reliable is [trustworthy short-step agency].
  Visual: intent -> bounded diff/action -> evidence.
  Cards: what changed, why it works, natural next question, harness moment.

3. Analogy
  Claim: Why can a reliable local step become a long-run component?
  Analogy: numerical methods / CI / compiler pipeline / control loop / transaction log.
  Boundary: local reliability is useful only when error/drift is bounded.

4. Talk route
  A numbered route so readers know the story before details.

5. Project highlight
  Claim: [System] is not [misleading category]; it is [correct mental model].
  Cards: reads state, delegates bounded work, enforces contracts.

6. Capability map
  Claim: The core capability is not [glamorous overclaim], but [boring durable value].
  Cards: 3-5 honest capabilities.

7. Domain generalization
  Claim: Same control plane, different task-specific prompts/roles/skills/artifacts.
  Visual: shared runtime center with domain-specific wrappers.

8. Repository / topology model
  Claim: [A/B/D split or equivalent] removes most confusion.
  Table: ID, role, runtime rule, why it matters.

9. System map
  Claim: Coarse architecture.
  Visual: repositories -> runtime loop -> agent roles -> verification gates -> persistence.

10. Tick loop / one bounded turn
  Claim: One tick is one bounded [research/service/debug] turn.
  Visual: read state -> route role -> act -> evidence -> gate -> persist/continue.

11. Gates and safety
  Claim: [Reviewers/artifact gate/scope audit] solve different problems.
  Table or diagram distinguishing gates.

12. Roles + skills
  Claim: Role routing controls who acts; skills control how specialized work is done.
  Visual: role responsibilities and skill injection.

13. Feedback / self-evolve
  Claim: Failures become reusable engine lessons only when evidence is structured.
  Evidence: commits, reports, state files, archived runs.

14. Reality / failure modes
  Claim: Longer loops expose new failure modes.
  Visual: global objective line vs wrong-direction local helper chain.
  Cards: wrong-direction diligence, fake closure, stale state, over-compression.

15. Why new infrastructure is needed
  Claim: Current model/training distribution is strong at short steps but weak at long-loop protocol.
  Metrics/cards: state, evidence, control, repair.

16. Ecosystem / benchmark landscape
  Claim: Peer systems and benchmarks ask different questions.
  Table: project/benchmark, core loop, what it preserves, contrast with this system.

17. Case evidence
  Repeat 2-4 case slides:
    Background: what is measured and why it is tricky.
    Case: what the system did.
    Evidence: figure + cards + metric strip + exact paths.

18. Roadmap / Q&A
  Claim: What remains hard, where human judgment still matters, and what the next repair loop should target.
```

## Slide Writing Blocks

### 1. Title Slide

Use when opening a deck or HTML tech share.

```html
<section class="slide active">
  <div class="eyebrow">[Tech Share] · [Date]</div>
  <h1>[System]: a [control plane] for [bounded long-loop work]</h1>
  <p class="subtitle">How [system] turns [workflow] into [event-planned, executor-driven, reviewable loop].</p>
  <div class="pillrow">
    <span class="pill">[runtime property]</span>
    <span class="pill">[agent property]</span>
    <span class="pill">[audit property]</span>
    <span class="pill">[extensibility property]</span>
  </div>
  <div class="footer"><span>[project / repo]</span><span class="slide-num"></span></div>
</section>
```

Writing rule: the title should be a mental model, not a feature list.

### 2. Historical Stage Strip

Use when explaining why this system appears now.

```html
<section class="slide">
  <div class="eyebrow">Warm-Up · [History Lens]</div>
  <h2>从 [old mode]，到 [new responsibility]</h2>
  <p>[System] 不是孤立出现的工程玩具。它更像是 [field/workflow] 走到 [stage] 以后，一个自然冒出来的问题：[question]？</p>
  <div class="stage-strip">
    <div class="stage-card"><b>1</b><strong>[Stage 1]</strong><span>[who executes, what is manual]</span></div>
    <div class="stage-card"><b>2</b><strong>[Stage 2]</strong><span>[closer to files/tools]</span></div>
    <div class="stage-card"><b>3</b><strong>[Stage 3]</strong><span>[trustworthy short-step behavior]</span></div>
    <div class="stage-card"><b>4</b><strong>[Stage 4]</strong><span>[harness/control-plane workflow]</span></div>
    <div class="stage-card"><b>5</b><strong>[Stage 5]</strong><span>[aspirational endpoint and why it is harder]</span></div>
  </div>
  <div class="thesis">我的判断：[realistic thesis]，而不是 [overclaim]. [cost/boundary reason].</div>
  <div class="footer"><span>[why this matters]</span><span class="slide-num"></span></div>
</section>
```

Writing rule: make the stage model opinionated. It should explain what is possible now and what is not.

### 3. Trustworthy Short Step

Use when bridging local agent competence to long-loop orchestration.

```text
Eyebrow: Stage [N] Breakthrough
Headline: [Local capability] 真正搭好的，是 “[trust primitive]” 的基石
Visual: intent -> bounded action/diff -> evidence -> state movement
Cards:
  - What changed: [new local capability]
  - Why it works: [training data / tooling / review habit]
  - Natural next question: [how to chain it]
  - Harness moment: [what keeps interrupting the loop]
Source note: analogy or evidence.
```

Writing rule: keep it about the smallest reliable unit of work.

### 4. Analogy Slide

Use to make the architecture feel necessary before implementation details.

```text
Eyebrow: Analogy · [Numerical Methods / CI / Transactions / Control Systems]
Headline: 为什么一个 [trusted local unit]，可以成为 [long workflow] 的组件？
Visual:
  - exact/ideal path vs approximate/agent path
  - error band / gate / rollback / convergence condition
Cards:
  - We do not inspect every step manually.
  - Local guarantees compose only under stability constraints.
  - The system's job is to keep drift bounded and visible.
Source note: cite analogy terms or external references if used.
```

Writing rule: use the analogy to explain one design constraint, not as decoration.

### 5. Talk Route / Reader Route

Use near the beginning.

```html
<section class="slide">
  <div class="eyebrow">Talk Route</div>
  <h2>从 [historical pressure]，走到 [system mechanism]</h2>
  <ol class="agenda">
    <li>为什么 [trusted short step] 自然导向 [harness/control plane]</li>
    <li>[System] 能承载哪些长循环任务</li>
    <li>[Topology], tick, reviewer, gate, audit 如何拼成一个循环</li>
    <li>[Self-evolve / failures] 暴露的长循环失败模式</li>
    <li>外部 [benchmarks/peer systems] 分别在问什么能力问题</li>
    <li>案例证据、诚实边界、roadmap，以及 QA 前的 runtime 讨论</li>
  </ol>
</section>
```

Writing rule: the route should preview the argument, not just list topics.

### 6. Project Highlight / Definition by Contrast

Use to lock the mental model.

```html
<section class="slide">
  <div class="eyebrow">[Project] Highlight</div>
  <h2>[System] is a [correct category], not a [misleading category]</h2>
  <div class="cards">
    <div class="card"><h3>Reads state</h3><p>[what state it reads]</p></div>
    <div class="card"><h3>Delegates bounded work</h3><p>[who plans, who executes, how bounded]</p></div>
    <div class="card"><h3>Enforces contracts</h3><p>[review/gate/scope/rollback/commit]</p></div>
  </div>
  <p>[The project-specific stack remains outside/inside as appropriate]. [System] watches, prompts, launches, reviews, persists, and asks humans for missing authority.</p>
</section>
```

Writing rule: use "not X, but Y" wherever readers often confuse the category.

### 7. Capability Map

Use to show honest scope.

```html
<div class="capability-grid">
  <div class="capability-card">
    <h3>[Capability 1]</h3>
    <p><b>[One-line value].</b> [Concrete workflow and evidence produced].</p>
  </div>
  <div class="capability-card">
    <h3>[Capability 2]</h3>
    <p><b>[One-line value].</b> [Concrete workflow and evidence produced].</p>
  </div>
  <div class="capability-card">
    <h3>[Capability 3]</h3>
    <p><b>[One-line value].</b> [Concrete workflow and evidence produced].</p>
  </div>
  <div class="capability-card">
    <h3>[Capability 4]</h3>
    <p><b>[One-line value].</b> [Concrete workflow and evidence produced].</p>
  </div>
</div>
```

Writing rule: "can do" means produces evidence, not just can talk about it.

### 8. Repository / Topology Table

Use when many misunderstandings come from where state lives.

```html
<table class="table">
  <tr><th>ID</th><th>Role</th><th>Runtime rule</th><th>Why it matters</th></tr>
  <tr><td>A</td><td>[Engine]</td><td>[templates/scripts; not live config after init]</td><td>[why separation matters]</td></tr>
  <tr><td>B</td><td>[Workspace]</td><td>[live source of runtime truth]</td><td>[plans, memory, logs, health, state]</td></tr>
  <tr><td>D</td><td>[Target]</td><td>[agent edits declared surfaces only]</td><td>[audit and rollback]</td></tr>
</table>
```

Writing rule: topology slides should remove future ambiguity, not teach filesystem trivia.

### 9. System Map

Use for architecture.

```text
Eyebrow: System Map
Headline: Coarse architecture
Visual layers:
  - Repository topology: engine, workspace, target, optional code graph
  - Runtime and agent loop: tick orchestrator, role router, provider plane, skill executor
  - Verification mechanisms: artifact gate, reviewers, scope audit, agent audit
  - Persistence/recovery: commit, push, rollback, archive
Speaker note:
  Emphasize separation between where the harness lives, where live state lives, and where experiments mutate code.
```

Writing rule: arrows should show responsibility and evidence flow, not every possible call edge.

### 10. Tick Loop

Use to explain one bounded turn.

```text
Eyebrow: Tick Loop
Headline: One tick is one bounded [research/debug/service] turn
Flow:
  read structured state
  decide route
  invoke role or deterministic hook
  produce bounded work/evidence
  run review/gates
  persist status or request human input
  stop/replan/continue
```

Writing rule: a tick is a unit of accountability. It should have a bounded action and evidence.

### 11. Gate / Safety Comparison

Use when people conflate checks.

```text
Eyebrow: Safety
Headline: [Gate A] and [Gate B] solve different problems
Table:
  Gate | Checks | Does not prove | Failure example
  artifact gate | required outputs exist | scientific validity | placeholder file
  scope audit | allowed files changed | result quality | correct file, wrong method
  reviewer | policy/science checks | execution completeness | good plan, no run
  completion fact | stop conditions satisfied | truth of scientific claim | stale evidence
```

Writing rule: every gate description needs a "does not prove" column.

### 12. Roles + Skills

Use when explaining agent organization.

```text
Eyebrow: Roles + Skills
Headline: Role routing controls who acts; skills control how specialized work is done
Matrix:
  Role | Question it answers | Should not own
  planner | what next? | machine ledgers
  reviewer | is plan/result acceptable? | inventing replacement goals
  executor | how to make progress? | final completion truth
  runtime/ledger | what is machine state? | scientific judgment
  skill | how to perform a specialized procedure? | task objective
```

Writing rule: roles are attention-shaping devices. Avoid making every role a status clerk.

### 13. Failure Mode Slide

Use to prevent overclaiming.

```text
Eyebrow: Harness Reality
Headline: 更长的循环也暴露了新的失败模式
Two columns:
  Typical problems:
    - wrong-direction diligence
    - fake closure / artifact theater
    - stale state read as current truth
    - local helper chain overwhelms global objective
  Likely causes:
    - too much context
    - close-turn training bias
    - missing single truth source
    - ambiguous gate semantics
Visual:
  global objective line vs drifting local helper path
Source note:
  Explain why this is a system design issue, not just model effort.
```

Writing rule: failure mode slides should be unsparing but useful. Each failure should imply a repair mechanism.

### 14. Why Infrastructure Is Needed

Use to restate philosophical core.

```text
Eyebrow: Why [Stage/System] Needs New Infrastructure
Headline: 当前 [model/data/workflow] 天然不擅长 [long-loop protocol]
Cards:
  Complexity: [new edge cases]
  Data gap: [short-step data vs long-loop traces]
  Golden harness: [how future traces could improve behavior]
Thesis:
  The value is not proving [full autonomy]. The value is putting [reliable short-step capability] into an honest, reviewable, rollbackable loop.
Metric strip:
  state | evidence | control | repair
```

Writing rule: this slide is the anti-hype anchor.

### 15. Ecosystem / Benchmark Table

Use to situate the system.

```html
<table class="table">
  <tr><th>Project / Benchmark</th><th>Core loop</th><th>What it preserves</th><th>Useful contrast</th></tr>
  <tr><td>[Peer 1]</td><td>[loop]</td><td>[artifacts]</td><td>[contrast with system]</td></tr>
  <tr><td>[Peer 2]</td><td>[loop]</td><td>[artifacts]</td><td>[contrast with system]</td></tr>
  <tr><td>[This system]</td><td>[loop]</td><td>[artifacts]</td><td>[control-plane-first / other thesis]</td></tr>
</table>
<p class="source-note">Representative references: [links]. Benchmarks measure systems; they are not always peer systems.</p>
```

Writing rule: say what the comparison is for. Avoid pretending all projects are on one leaderboard.

### 16. Case Evidence Slide

Use for real runs.

```html
<section class="slide">
  <div class="eyebrow">Case [N] · [Project / Domain]</div>
  <h2>[System] [did concrete thing] across [hard condition]</h2>
  <div class="case-layout">
    <img class="case-figure" alt="[figure description]" src="[relative/path/to/figure.png]">
    <div class="case-side">
      <div class="card"><h3>Case introduction</h3><p>[task, setup, why it matters]</p></div>
      <div class="card"><h3>Why it is shareable</h3><p>[generalizable design lesson]</p></div>
      <div class="card"><h3>Reviewer correction / honest gap</h3><p>[what failed, what was corrected, or what remains missing]</p></div>
      <div class="statline">
        <div class="statbox"><b>[metric/path]</b><span>[meaning]</span></div>
        <div class="statbox"><b>[delta/count]</b><span>[meaning]</span></div>
        <div class="statbox"><b>[evidence]</b><span>[meaning]</span></div>
      </div>
    </div>
  </div>
  <div class="footer"><span>Evidence: [exact path / commit / output bundle]</span><span class="slide-num"></span></div>
</section>
```

Writing rule: a case is not a story unless it has evidence paths and a correction/honest gap.

## HTML Deck Shell

Use this minimal shell when creating a HARP-tech-share-style standalone HTML deck. Keep the CSS restrained and content-oriented.

```html
<!doctype html>
<html lang="[en/zh-CN]">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>[Deck title]</title>
  <style>
    :root {
      --ink: #111827;
      --muted: #526071;
      --line: #d9e0ea;
      --panel: #f7f9fc;
      --blue: #1d4ed8;
      --green: #047857;
      --red: #b91c1c;
      --shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; height: 100%; background: #e8edf4; color: var(--ink); font-family: Arial, Helvetica, sans-serif; }
    body { overflow: hidden; }
    .deck { height: 100vh; width: 100vw; display: grid; place-items: center; padding: 14px; }
    .slide {
      display: none;
      width: min(1680px, 100%);
      height: min(940px, calc(100vh - 28px));
      background: #fff;
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      padding: 42px 48px;
      position: relative;
      overflow: hidden;
    }
    .slide.active { display: block; }
    .eyebrow { color: var(--blue); font-size: 15px; font-weight: 700; margin-bottom: 14px; }
    h1, h2 { margin: 0; letter-spacing: 0; }
    h1 { font-size: 58px; line-height: 1.04; max-width: 940px; }
    h2 { font-size: 38px; line-height: 1.12; max-width: 1000px; }
    p { font-size: 21px; line-height: 1.42; color: var(--muted); margin: 18px 0 0; max-width: 940px; }
    .subtitle { font-size: 25px; color: #334155; max-width: 960px; }
    .footer { position: absolute; left: 48px; right: 48px; bottom: 28px; display: flex; justify-content: space-between; color: #64748b; font-size: 13px; }
    .cards, .capability-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; margin-top: 32px; }
    .card, .capability-card { border: 1px solid var(--line); background: var(--panel); border-radius: 8px; padding: 20px; }
    .card h3, .capability-card h3 { margin: 0 0 10px; font-size: 21px; }
    .card p, .capability-card p { font-size: 16px; line-height: 1.35; margin: 0; color: var(--muted); }
    .pillrow { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 26px; }
    .pill { border: 1px solid var(--line); border-radius: 999px; padding: 8px 12px; color: #334155; background: #f8fafc; font-size: 15px; }
    .thesis { border-left: 5px solid var(--green); padding: 18px 22px; margin-top: 24px; background: #f0fdf4; color: #1f2937; font-size: 22px; line-height: 1.38; max-width: 1040px; }
    .table { border-collapse: collapse; margin-top: 28px; width: 100%; font-size: 17px; }
    .table th, .table td { border-bottom: 1px solid var(--line); padding: 13px 12px; text-align: left; vertical-align: top; }
    .table th { color: #334155; background: #f8fafc; }
    .case-layout { display: grid; grid-template-columns: 1.18fr 0.82fr; gap: 24px; align-items: start; margin-top: 24px; }
    .case-figure { width: 100%; height: 555px; object-fit: contain; border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 6px; }
    .statline { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 16px; }
    .statbox { border: 1px solid var(--line); border-radius: 8px; background: #f8fafc; padding: 13px; }
    .statbox b { display: block; color: var(--ink); font-size: 23px; margin-bottom: 3px; }
    .source-note { color: #64748b; font-size: 13px; line-height: 1.35; margin-top: 12px; }
    .navhint { position: fixed; right: 22px; bottom: 14px; color: #64748b; font-size: 12px; }
    @media print {
      body { overflow: visible; background: white; }
      .deck { display: block; padding: 0; height: auto; }
      .slide { display: block !important; page-break-after: always; width: 100vw; height: 100vh; box-shadow: none; border: 0; }
      .navhint { display: none; }
    }
  </style>
</head>
<body>
  <main class="deck">
    [slides]
  </main>
  <div class="navhint">Use ← / →</div>
  <script>
    const slides = Array.from(document.querySelectorAll('.slide'));
    let idx = 0;
    function show(n) {
      idx = Math.max(0, Math.min(slides.length - 1, n));
      slides.forEach((s, i) => s.classList.toggle('active', i === idx));
      document.querySelectorAll('.slide-num').forEach(el => {
        el.textContent = `${idx + 1} / ${slides.length}`;
      });
    }
    window.addEventListener('keydown', e => {
      if (e.key === 'ArrowRight' || e.key === 'PageDown') show(idx + 1);
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') show(idx - 1);
    });
    show(0);
  </script>
</body>
</html>
```

## Long-Form HTML Truth Source Variant

If the deliverable is not a slide deck, convert the same deck logic into long-form chapters:

```text
0. Recent Update
1. Why this system exists
2. What this system is not
3. Truth sources and ownership
4. Role boundaries
5. One runtime loop
6. Gate/safety layers
7. Current-status deconfusion
8. Failure modes and repair mechanisms
9. Case evidence / postmortem evidence
10. Overall architecture map and maintenance rules
```

Keep the final chapter as a human/agent alignment surface:

- architecture diagram
- state-write boundaries
- tick sequence
- design details
- common misunderstandings
- document maintenance trigger

## Final Pass Checklist

- The opening explains why the system became necessary.
- The title defines the system by contrast.
- The route slide/chapter lets readers predict the argument.
- Every architecture detail answers a human confusion.
- Every case has evidence paths or metrics.
- Every gate says what it does not prove.
- Failure modes are tied to repair mechanisms.
- The ending tells future agents how not to misread the project.
