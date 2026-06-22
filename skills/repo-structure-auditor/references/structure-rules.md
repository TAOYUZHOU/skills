# Repository Structure Rules

Use these rules as evidence prompts, not as automatic truth. Always verify candidates against project size, explicit architecture docs, framework conventions, and existing naming patterns.

## Two-Layer Detection

Layer 1 finds candidates mechanically:

- stack signals from manifests and config
- framework placement mismatches
- source files in root when a `src/` layout exists
- mixed generic directories
- inconsistent domain/layer substructure

Layer 2 verifies context:

- small projects do not need full domain/layer decomposition
- mixed monorepos are acceptable when packages/apps are clearly separated
- framework conventions apply only when that framework is detected
- documented decisions suppress findings unless code drifted from the decision
- generated, vendored, test fixture, and example directories should not drive architecture findings

## Framework Placement

### JavaScript and TypeScript

Signals: `package.json`, `tsconfig*.json`, Vite/Next/Vue/Nest/Express config.

Expected:

- app source under `src/`, `app/`, `pages/`, `packages/`, or `apps/`
- tests under `test/`, `tests/`, `__tests__/`, or colocated `*.test.*`
- reusable UI under `components/`
- hooks in `hooks/`
- shared utilities in small, cohesive `lib/` or `utils/`

Flag:

- many implementation files in repo root
- API/server code under UI component directories
- React/Vue components scattered outside the app source tree
- several unrelated data-fetching or error-handling patterns in parallel

### Python

Signals: `pyproject.toml`, `setup.py`, `requirements.txt`, `uv.lock`.

Expected:

- source under `src/<package>/` or a clearly named package directory
- tests under `tests/` or colocated by convention
- API/routing, services, models, and data access separated when project size justifies it

Flag:

- substantial package code in repo root
- scripts that duplicate package logic instead of importing it
- service/data/model responsibilities mixed in one broad module

### Go

Signals: `go.mod`.

Expected:

- `cmd/` for binaries in multi-binary projects
- `internal/` for private app packages
- `pkg/` only for intended public/reusable packages
- tests beside packages

Flag:

- many source files in root for multi-package projects
- exported packages under `pkg/` that are only used internally
- unclear command/package boundaries

### Rust

Signals: `Cargo.toml`.

Expected:

- `src/`, optional `src/bin/`, `tests/`, `benches/`
- workspace crates under clear member directories

Flag:

- workspace members without clear crate boundaries
- integration tests mixed into unrelated source directories

## Layer and Domain Layout

When a project has clear domains or layers, check for consistency.

Common layer names:

- domain/entities/models
- application/use-cases/services
- adapters/controllers/routes/handlers
- infrastructure/persistence/repositories/clients
- shared/common/lib

Flag as `ALIGN_DOMAIN_STRUCTURE` when:

- some domains have clear sublayers and others flatten unrelated responsibilities
- controllers/routes reach directly into persistence while peer modules use services/use cases
- infrastructure concerns leak into domain/application folders
- the repo appears to intend Clean Architecture, hexagonal architecture, DDD, or feature modules but only partially follows it

## Junk Drawer Directories

Generic names are not inherently bad. They become findings when they are large, high-fan-in, or mixed.

Watch names:

- `utils`
- `helpers`
- `common`
- `shared`
- `lib`
- `services`
- `misc`

Flag as `SPLIT_JUNK_DRAWER` when:

- directory has more than 10 implementation files
- filenames span three or more unrelated responsibilities
- it mixes UI, data access, formatting, IO, business rules, and framework glue
- imports point to it from many unrelated areas

Prefer recommendations such as:

- split by domain (`billing/`, `users/`, `reports/`)
- split by responsibility (`date-formatting`, `http-client`, `validation`)
- move framework glue outward and pure helpers inward

## Report Quality Bar

Each finding must include:

- action label
- severity
- confidence
- effort estimate
- evidence paths
- why it matters
- recommended move/split/alignment
- verification gate for a future implementation

Do not report:

- generated folders, vendored code, dependencies, snapshots, fixtures, or build outputs as architecture drift
- single-file convenience dirs in small projects
- choices explicitly documented in architecture decisions unless the code contradicts the decision
