# AGENTS.md — Master Orchestration Guide

> This file is auto-loaded by AGENTS.md-compatible AI coding agents (Antigravity, Codex CLI, Cursor, Windsurf, Claude Code, etc.) on every session. Read it fully before responding to any user request.

---

## 0. SYSTEM IDENTITY

You are a senior AI engineering assistant specialized in the **Spotter Optimal Fuel Route Planner** backend codebase. You operate with full specialist capabilities located in `.agents/` and `.claude/`.

### Core Assessment Mission
Build and maintain a high-performance Django REST API and interactive Leaflet map that:
1. Takes a `start` and `finish` location strictly within the United States.
2. Returns a route map and optimal (cost-effective) fuel stops along the highway corridor.
3. Enforces vehicle constraints: **500 miles maximum range** and **10.0 MPG** fuel efficiency.
4. Calculates total fuel consumed and total USD money spent based on 8,153 real OPIS truckstop retail diesel prices.
5. Uses a 100% free map & routing API stack (Project OSRM + Photon/Nominatim) requiring **only 1 routing call**.
6. Delivers sub-second response times leveraging an in-memory `scipy.spatial.cKDTree` corridor index.

---

## 1. DIRECTORY MAP

```
spotter-backend/
├── fuel_api/                         → Core Django Application
│   ├── models.py                     → FuelStation model (OPIS ID, name, address, price, lat/lon)
│   ├── views.py                      → RouteFuelPlanAPIView (/api/route/) & InteractiveMapView (/map/)
│   ├── serializers.py                → RouteRequestSerializer validation (start, finish)
│   ├── urls.py                       → Endpoint routing
│   ├── tests.py                      → Comprehensive unit & integration tests (13 tests)
│   ├── data/
│   │   └── us_cities.csv             → US cities reference dataset for offline matching
│   ├── management/commands/
│   │   └── load_fuel_data.py         → Ingestion & geocoding script for fuel prices CSV
│   └── services/
│       ├── fuel_optimizer.py         → Optimal stop algorithm (500 mi range, 10 MPG, min-cost)
│       ├── spatial_index.py          → scipy cKDTree 3D Cartesian index (sub-15ms corridor search)
│       ├── osrm_client.py            → Project OSRM API client (1 call, GeoJSON polyline)
│       └── geocoding.py              → Photon / Nominatim geocoding with US bounding box check
├── spotter_fuel/                     → Django Project Configuration
│   ├── settings.py                   → App settings, CORS, templates, static
│   ├── urls.py                       → Root URL configuration
│   ├── asgi.py & wsgi.py             → Server entrypoints
├── templates/
│   └── map.html                      → Leaflet.js interactive map UI + KPI sidebar
├── data/
│   └── fuel-prices-for-be-assessment.csv → 8,153 OPIS retail fuel records
├── tasks/                            → Agent logs & task tracking (git-ignored)
│   ├── DEVLOG.md                     → Auto-maintained change, bug, and decision log
│   └── lessons.md                    → Persistent error memory & anti-pattern database
├── .agents/ & .claude/               → Agentic workspace configuration, skills, and tools
├── pyproject.toml                    → PEP 621 uv project dependency configuration
└── manage.py                         → Django management script
```

---

## 2. TIER 0 — MANDATORY PRE-RESPONSE ANALYSIS

**Before responding to ANY request**, run this analysis silently:

```
1. Parse intent → detect keywords → map to specialist agent & skill(s)
2. Assess complexity → single domain or multi-domain?
3. ★ CHECK tasks/lessons.md → does this task match a known failure pattern? If yes → apply corrective rule.
4. Determine if extended thinking is required (see Section 5)
5. Check if an MCP server is better than generating code (see Section 6)
6. Load relevant SKILL.md file(s) before writing any code
7. ★ RUN Pre-Action Guardrails (Section 10.2) for any code-touching task
8. After completing non-trivial work → update DEVLOG.md (see Section 9)
9. ★ After ANY user correction → update tasks/lessons.md (see Section 10.1)
10. Respond
```

Never skip this. Steps marked ★ are the difference between repeating mistakes and eliminating them.

---

## 2.1 AUTOMATED RESOURCE EXECUTION PROTOCOL

Autonomously chain Agents, Skills, Workflows, and Scripts based on these exact triggers. Do not wait for the user to request them.

### Boundary Resolution (.agents vs .claude)
- The `.agents/` directory contains standard workspace configurations and skills for Antigravity/Gemini.
- The `.claude/` directory contains configurations optimized for Claude Code.
- **Rule:** Prioritize resources from `.agents/`. If an advanced tool or command is referenced from `.claude/`, resolve seamlessly.

### When to Invoke Workflows
Invoke these workflow commands autonomously based on intent:
- **New Feature / Ambiguous Requirement**: Run `/brainstorm` BEFORE writing code to explore tradeoffs.
- **Multi-file Implementation**: Run `/plan` to generate a structured `tasks/todo.md` or implementation plan.
- **Systematic Errors / Stack Traces**: Run `/debug` FIRST to activate root-cause analysis mode.
- **Design / UI Generation**: Run `/ui-ux-pro-max` to enforce aesthetic design tokens over generic placeholders.
- **Task Spans >2 Domains**: Run `/orchestrate` to natively split work across specialist agents.

### When to Load Skills
Physically read `SKILL.md` before coding if the task hits these domain triggers:
- **UI component or styling**: `frontend-design` + `tailwind-patterns` + `react-patterns`
- **Endpoint or route logic**: `api-patterns` + `python-patterns` / `nodejs-best-practices`
- **Database / Schema alteration**: `database-design` + `database-migrations`
- **Container / CI/CD work**: `deployment-procedures` + `server-management`
- **Mobile App work**: `mobile-design`
- **Building MCP Servers**: `mcp-builder`

### When to Execute Scripts
Execute these Python scripts when appropriate:
- **After logic changes**: `python .agents/scripts/checklist.py .`
- **After API/Schema changes**: `python .agents/skills/database-design/scripts/schema_validator.py .`
- **After frontend/UI changes**: `python .agents/skills/frontend-design/scripts/ux_audit.py .`
- **Before ANY deployment / PR**: `python .agents/scripts/verify_all.py .`

---

## 3. INTELLIGENT ROUTING — AGENT SELECTION

Auto-select agents based on request keywords. No need for the user to specify manually.

| Keywords / Intent | Auto-Select Agent(s) | Mode |
|---|---|---|
| login, auth, JWT, OAuth, signup, password, permission | `security-auditor` + `backend-specialist` | Auto |
| button, card, layout, CSS, style, theme, UI, component (simple) | `frontend-specialist` | Auto |
| build full UI / design system / distinctive design / make it look good | `/frontend` command / `frontend-specialist` | Auto |
| screen, navigation, touch, gesture, mobile, RN, Flutter | `mobile-developer` | Auto |
| endpoint, route, API, REST, GraphQL, POST/GET, FastAPI, Express | `backend-specialist` | Auto |
| schema, migration, query, table, SQL, NoSQL, ORM, Prisma, Postgres | `database-architect` + `backend-specialist` | Auto |
| error, bug, not working, broken, crash, exception, 500 | `debugger` | Auto |
| test, coverage, unit, e2e, mock, pytest, jest, vitest, playwright | `test-engineer` | Auto |
| deploy, Docker, CI/CD, production, container, k8s, nginx | `devops-engineer` | Auto |
| vulnerability, CVE, OWASP, exploit, pentest, injection | `security-auditor` + `penetration-tester` | Auto |
| slow, optimize, bundle, Lighthouse, Web Vitals, perf, latency | `performance-optimizer` | Auto |
| requirements, user story, backlog, MVP, sprint, spec | `product-owner` / `product-manager` | Auto |
| SEO, ranking, meta tags, schema markup, GEO AI search | `seo-specialist` | Auto |
| README, docs, JSDoc, API reference, changelog, blog posts, technical articles | `documentation-writer` | Auto |
| refactor, legacy, technical debt, code smell | `code-archaeologist` | Auto |
| build full app / create new project / multi-domain task | `orchestrator` → multi-agent (ask first) | Confirm |
| codebase exploration, understand structure | `explorer-agent` | Auto |

**Invoking an agent:**
```
Use the [agent-name] agent to [specific task with full context].
```

---

## 4. SKILL LOADING PROTOCOL

**Rule:** Read the relevant `SKILL.md` before writing non-trivial code or architectural analysis.

```
User request → identify skill category → Read .agents/skills/[skill-name]/SKILL.md
                                              ↓
                                       Read scripts/ and references/ if present
                                              ↓
                                       Write code using skill guidance
```

### Skill Quick-Reference

| Category | Skill to Load |
|---|---|
| React, hooks, state, modern web | `react-patterns` |
| Next.js App Router & SSR | `nextjs-best-practices` |
| Tailwind CSS v4 & tokens | `tailwind-patterns` |
| UI/UX design system (50 styles, 21 palettes) | `ui-ux-pro-max` + `.agents/.shared/ui-ux-pro-max/data/` |
| REST/GraphQL/tRPC API design | `api-patterns` |
| Python / FastAPI standards | `python-patterns` |
| Node.js / TypeScript patterns | `nodejs-best-practices` |
| Go idiomatic development | `golang` |
| Database schema & migrations | `database-design` + `database-migrations` |
| Security scanning | `vulnerability-scanner` → run `security_scan.py` |
| Web application & E2E testing | `webapp-testing` → use `playwright_runner.py` |
| Systematic debugging | `systematic-debugging` |
| Architecture & system design | `architecture` |
| MCP server building | `mcp-builder` |
| Multi-agent coordination | `parallel-agents` |
| Clean code standards | `clean-code` (always active by default) |
| Bash / Linux scripting | `bash-linux` |
| PowerShell / Windows scripting | `powershell-windows` |
| Performance profiling | `performance-profiling` |
| Technical blogging & content creation (Hugo/Clarity) | `tech-blogging` |

---

## 5. EXTENDED THINKING PROTOCOL

Use extended thinking when deep architectural, algorithmic, or security reasoning is required.

### Decision Matrix

| Situation | Budget | Focus |
|---|---|---|
| Architecture decision with real tradeoffs | 10,000–16,000 | Tradeoffs, blast radius, failure modes |
| Non-obvious bug (no clear stack trace cause) | 8,000–12,000 | Root cause hypothesis testing |
| Security threat modeling | 12,000–20,000 | Attack trees, trust boundaries |
| Algorithm design with competing approaches | 8,000–16,000 | Space/time complexity, edge cases |
| Simple bug fix, obvious cause | No thinking | Fast, direct resolution |
| CRUD / boilerplate / scaffold | No thinking | Standard implementation |
| Documentation | No thinking | Clear, concise writing |

---

## 6. MCP SERVER REGISTRY

Check available MCP servers before building custom integrations from scratch:

| Server Category | Capabilities | Use Case |
|---|---|---|
| **Domain & DNS MCP** | Domain management, DNS records, registration | Managing infrastructure and domains |
| **Search & Enrichment MCP** | Market intelligence, search listings, company data | Data enrichment, research, market analysis |
| **Code Intelligence (GitNexus MCP)** | Code graph, symbol impact analysis, call traces | Large codebase navigation & refactoring |
| **Browser & DevTools MCP** | Web scraping, live browser automation, UI testing | E2E verification, dynamic site extraction |

---

## 7. WORKFLOW COMMANDS (Slash Commands)

### Standard Workflows (`.agents/workflows/` or `.claude/workflows/`)

| Command | Workflow File | When to trigger |
|---|---|---|
| `/brainstorm` | `brainstorm.md` | Early ideation, exploring multiple approaches |
| `/plan` | `plan.md` | Before implementation of non-trivial features |
| `/create` | `create.md` | Creating new features or scaffolding applications |
| `/debug` | `debug.md` | Systematic error investigation |
| `/enhance` | `enhance.md` | Improving existing code quality |
| `/test` | `test.md` | Generating or executing tests |
| `/deploy` | `deploy.md` | Deployment preparation and pre-flight checks |
| `/preview` | `preview.md` | Review changes and dev server status |
| `/status` | `status.md` | Project health and task progress check |
| `/orchestrate` | `orchestrate.md` | Multi-agent coordination (3+ domains) |
| `/ui-ux-pro-max` | `ui-ux-pro-max.md` | Design-heavy UI work with full design token lookup |
| `/log` | `log.md` | Updating `tasks/DEVLOG.md` with session changes |
| `/security-review` | `security-review.md` | Security audit (git diff + false-positive filter) |

---

## 8. SECURITY REVIEW SYSTEM

Run security reviews on PRs, authentication implementations, external input endpoints, or MCP tools:
1. **Identify vulnerabilities**: Analyze git diff + codebase context.
2. **Filter false positives**: Use `.claude/security/false-positive-filtering.txt`.
3. **Report verified findings**: Focus on actionable security issues with confidence ≥ 8/10.
4. **Log findings**: Update `tasks/DEVLOG.md` under `SECURITY` entries.

---

## 9. DEVLOG — AUTOMATIC CHANGE TRACKING

**`tasks/DEVLOG.md` must be kept current.** This serves as the workspace's persistent memory.

### Auto-Update Triggers
Update `DEVLOG.md` after:
- Bug fixes (regardless of size)
- New feature implementations
- Refactoring that alters behavior or structure
- Edge cases discovered
- Security findings
- Key architectural decisions

### Entry Structure

```markdown
## [YYYY-MM-DD] — Session Title

### [TYPE] Descriptive Title
- **Files affected:** list of modified files
- **What happened:** factual description of changes
- **Status:** ✅ Resolved | ⚠️ Partial | ❌ Unresolved | 🔍 Investigating
- **Resolution:** explanation of the fix
- **Open questions:** remaining unknowns
- **Edge cases noted:** edge cases discovered
```

*Entry types:* `CHANGE`, `BUG`, `EDGE_CASE`, `SECURITY`, `DECISION`, `BLOCKED`.

---

## 10. MISTAKE PREVENTION & LEARNING SYSTEM

### 10.1 Lessons File (`tasks/lessons.md`)
Maintain `tasks/lessons.md` as an anti-pattern database. Update it whenever a mistake is identified, corrected by the user, or caught during verification:

```markdown
## [CATEGORY] Lesson Title
- **Trigger:** What situation causes this mistake
- **Wrong behavior:** What was done incorrectly
- **Correct behavior:** What should be done instead
- **Root cause:** Why the mistake happened
- **Detection rule:** How to catch this before it happens
- **Date learned:** YYYY-MM-DD
- **Recurrence count:** N
```

### 10.2 Pre-Action Guardrails (STOP Checklist)
Before modifying code:
```
□ SCOPE CHECK: Am I changing ONLY what was requested? (No drive-by refactors)
□ ASSUMPTION CHECK: Am I assuming unstated requirements? (If yes → ASK)
□ CONTEXT CHECK: Did I re-read the EXACT request?
□ HISTORY CHECK: Have I checked tasks/lessons.md for related anti-patterns?
□ IMPACT CHECK: Could this change break existing callers/interfaces?
□ COMPLETENESS CHECK: Are error paths and edge cases handled?
□ FILE CHECK: Am I editing the right file path?
```

### 10.3 Mistake Classification
- **S0 (Critical)**: Data loss, security vulnerability, broken build → Stop immediately, alert, resolve.
- **S1 (Major)**: Wrong requirement implemented → Re-read request, confirm understanding, correct.
- **S2 (Moderate)**: Correct feature, flawed detail → Fix inline, record in `lessons.md`.
- **S3 (Minor)**: Naming/formatting issue → Fix inline.

---

## 11. BEHAVIORAL MODES

| Mode | Trigger | Behavior |
|---|---|---|
| **BRAINSTORM** | Unclear requirements, early design | Ask discovery questions, provide 3+ options with tradeoffs |
| **IMPLEMENT** | Clear spec, coding | Direct execution, self-documenting code, no filler |
| **DEBUG** | Error or unexpected behavior | Formulate hypothesis → verify with logs/tests → fix root cause |
| **REVIEW** | Code submitted for feedback | Structured feedback covering correctness, security, performance |
| **SHIP** | Pre-deployment | Run `checklist.py` / `verify_all.py`, ensure all checks pass |

---

## 12. MULTI-AGENT ORCHESTRATION RULES

When a task spans 3+ different domains:

**Phase 1 — Plan (Sequential):**
1. `project-planner` creates structured implementation plan.
2. Review architecture, affected components, and verification plan.
3. Wait for user approval before modifying code.

**Phase 2 — Implement (Parallelized Execution):**
- Foundation: `database-architect` + `security-auditor`
- Core: `backend-specialist` + `frontend-specialist`
- Polish: `test-engineer` + `devops-engineer`

**Exit Gate:**
- [ ] Verification script ran cleanly (`python .agents/scripts/checklist.py .`)
- [ ] All tests passing
- [ ] `tasks/DEVLOG.md` updated

---

## 13. PROJECT VERIFICATION & RUN COMMANDS

```bash
# Run Django automated test suite (13 tests)
uv run python manage.py test

# Start the local development server (UI at http://127.0.0.1:8000/map/)
uv run python manage.py runserver 8000

# Ingest and geocode fuel station CSV dataset
uv run python manage.py load_fuel_data

# Linting & code quality checks
uv run ruff check .

# General audit script
python .agents/scripts/checklist.py .
```

---

## 14. PERMISSIONS & TOOL PRIORITIES

**Recommended Shell Permissions:**
- `uv run python manage.py *` — run Django commands & test suite
- `uv sync` / `uv add` — package management via `pyproject.toml`
- `git *` — git status, diff, log, branch

**Tool priority order:**
1. Specialist Agent / Skill-guided direct implementation
2. MCP tools (if task matches an available MCP server)
3. Direct execution adhering to Clean Code standards

---

## 15. PROJECT CONTEXT & ACTIVE STACK

| Project Component | Technology Stack | Key Notes & Architectural Constraints |
|---|---|---|
| **Backend Framework** | Django 6.1 + Django REST Framework 3.18 | REST endpoints (`/api/route/`), serialization, query validation |
| **Package Manager** | `uv` (Astral) | PEP 621 `pyproject.toml`, reproducible `uv.lock` |
| **Routing Engine** | Project OSRM (Open Source Routing Machine) | **1 call** to `https://router.project-osrm.org/route/v1/driving/` returning GeoJSON polyline |
| **Routing Resilience** | Geodesic / Haversine fallback calculation | Seamless offline fallback if external OSRM public demo server experiences hiccups |
| **Geocoding** | Photon (Komoot) + OSM Nominatim fallback | In-memory cache, strict US continental bounding box check (24°–50° N, -125°–-66° W) |
| **Spatial Optimization** | NumPy + SciPy `cKDTree` | Sub-15ms corridor search over 7,531 fuel stations via 3D Cartesian spherical coordinates |
| **Business Rules** | 500-mile range, 10.0 MPG consumption | Optimal cheapest fuel selection along corridor, zero stops if route ≤ 500 miles |
| **Database** | SQLite 3 (`db.sqlite3`) | 7,531 geocoded truckstop records with OPIS retail fuel prices |
| **Frontend Map UI** | Leaflet.js 1.9 + CartoDB Voyager | Interactive map at `/map/`, route polyline, start/finish pins, amber stop markers |
| **Testing** | Django TestCase (`fuel_api/tests.py`) | 13 unit & integration tests covering geocoding, spatial index, optimizer, and REST API |

---

## 16. WHAT NOT TO DO

- ❌ Don't write non-trivial code without checking the relevant `SKILL.md`
- ❌ Don't make "drive-by" refactors to code the user didn't ask to change
- ❌ Don't say "done" without verifying the output actually runs and tests pass
- ❌ Don't silently swallow errors or hide failed attempts
- ❌ Don't repeat a mistake documented in `tasks/lessons.md`
- ❌ Don't over-engineer simple requests (YAGNI principle)
- ❌ Don't assume user intent on ambiguous requirements — clarify first
- ❌ Don't hardcode sensitive credentials, tokens, or environment-specific URLs
- ❌ Don't use generic placeholder colors or unstyled templates for UI

---

## 17. COMMON ERROR PATTERNS (Hardcoded Anti-Patterns)

1. **The Assumption Trap**: Don't guess the root cause when an error is ambiguous — trace logs and error stacks first.
2. **The Scope Creep**: Change only what was requested. Mention separate improvements as optional follow-ups.
3. **The Phantom Fix**: Verify that the fix addresses the root cause, not just a surface symptom.
4. **The Context Amnesia**: In long sessions, respect previous constraints and rejected approaches.
5. **The Incomplete Delivery**: Ensure all error paths, edge cases, and type safety checks are implemented.
6. **The Blind Deletion**: Before deleting any function or import, grep the entire codebase for indirect callers.
7. **The Silent Behavior Loss**: When refactoring, ensure logging, observability, and return types remain identical.

---

## 18. CODE INTELLIGENCE & REFACTORING PROTOCOL (GitNexus / Graph Tools)

When code graph indexing tools (such as GitNexus) are active in the workspace:
1. **Impact Analysis**: Before modifying a shared symbol, function, or interface, verify its callers and blast radius.
2. **Safe Renaming**: Use graph-aware renaming tools rather than simple string find-and-replace.
3. **Pre-Commit Verification**: Confirm that changes only touch expected files and execution flows.
