# Research & Report Agent Repository Bootstrap Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a standalone GitHub repository containing the approved Python + LangGraph design and GitHub best-practice project hygiene.

**Architecture:** The repository starts as a design-first Python project. The implementation will live under `src/research_report_agent`, tests under `tests`, and the authoritative architecture in `docs/spec/design.md`. GitHub Actions will validate formatting, linting, and tests before merges to `main`.

**Tech Stack:** Python 3.11, LangGraph, Pydantic, pytest, Ruff, GitHub CLI, GitHub Actions.

**Spec:** `docs/spec/design.md`

## Global Constraints

- Default branch is `main`.
- Repository visibility is private unless the owner explicitly requests public.
- All merges to `main` use squash merges.
- Head branches are deleted after merge.
- CI must run Ruff and pytest on every pull request.
- No secrets may be committed.
- Design-first implementation follows the approved Guardrail Agent and LangGraph architecture.

---

### Task 1: Initialize the repository foundation

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `pyproject.toml`

**Interfaces:**
- Consumes: approved design from `docs/spec/design.md`
- Produces: Python package metadata for future `src/research_report_agent` implementation

- [x] **Step 1: Initialize a standalone Git repository on `main`**

Run: `git init -b main`

Expected: Git reports an initialized repository.

- [x] **Step 2: Add repository metadata and safety ignore rules**

Create the four foundation files listed above.

- [x] **Step 3: Verify no generated or secret files are staged**

Run: `git status --short`

Expected: only intentional repository files appear.

- [x] **Step 4: Commit**

Run: `git add README.md LICENSE .gitignore pyproject.toml && git commit -m "chore: initialize repository"`

### Task 2: Publish the approved design specification

**Files:**
- Create: `docs/spec/design.md`
- Create: `docs/plans/2026-08-16-repository-bootstrap.md`

**Interfaces:**
- Consumes: the approved Guardrail Agent and Python + LangGraph decisions
- Produces: the authoritative implementation specification

- [x] **Step 1: Copy the approved specification**

Copy the approved design into `docs/spec/design.md`.

- [x] **Step 2: Record the repository bootstrap plan**

Create this implementation plan under `docs/plans/`.

- [x] **Step 3: Review the specification for guardrail and stack requirements**

Run: `grep -n "Guardrail Agent\\|Python + LangGraph" docs/spec/design.md`

Expected: both requirements are present.

- [x] **Step 4: Commit**

Run: `git add docs && git commit -m "docs: add research agent design specification"`

### Task 3: Add GitHub community health files

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/CODEOWNERS`

**Interfaces:**
- Consumes: Python 3.11 and GitHub flow decisions
- Produces: contribution, disclosure, review, and ownership conventions

- [x] **Step 1: Add contribution and security guidance**

Create `CONTRIBUTING.md` and `SECURITY.md`.

- [x] **Step 2: Add issue and pull request templates**

Create the GitHub templates.

- [x] **Step 3: Add a code owner**

Create `.github/CODEOWNERS` using the repository owner.

- [x] **Step 4: Commit**

Run: `git add CONTRIBUTING.md SECURITY.md .github && git commit -m "docs: add community health files"`

### Task 4: Add CI and dependency automation

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/dependabot.yml`

**Interfaces:**
- Consumes: Python 3.11, Ruff, and pytest project metadata
- Produces: pull request validation and weekly dependency update PRs

- [x] **Step 1: Add CI workflow**

Create `.github/workflows/ci.yml` to install Python 3.11, install dependencies, run Ruff format check, lint, and pytest.

- [x] **Step 2: Add Dependabot configuration**

Create `.github/dependabot.yml` for pip and GitHub Actions ecosystems.

- [x] **Step 3: Validate workflow YAML**

Run: `python3 -c "import yaml, pathlib; [yaml.safe_load(p.read_text()) for p in pathlib.Path('.github').rglob('*.yml')]"` if PyYAML is available.

- [x] **Step 4: Commit**

Run: `git add .github && git commit -m "ci: add validation and dependency automation"`

### Task 5: Create and protect the GitHub repository

**Files:**
- No source file changes

**Interfaces:**
- Consumes: authenticated GitHub CLI session
- Produces: private GitHub repository with `main` protection

- [x] **Step 1: Authenticate GitHub CLI**

Run: `gh auth login --hostname github.com --web --git-protocol https`

Expected: `gh auth status` reports a valid account.

- [x] **Step 2: Create the private repository**

Run: `gh repo create research-report-agent --private --source . --remote origin --push`

Expected: repository is created and `main` is pushed.

- [x] **Step 3: Configure repository merge policy**

Use GitHub CLI/API to enable squash merge and disable merge commits and rebase merges.

- [x] **Step 4: Protect `main`**

Require pull requests, successful CI, linear history, and branch deletion before merge.

Outcome: after the owner made the repository public, branch protection was enabled successfully on `main`. The protected branch requires a pull request, one approving code-owner review, up-to-date CI checks, linear history, conversation resolution, and protection from force pushes and deletion. Administrator bypasses are disabled.

- [x] **Step 5: Verify remote repository**

Run: `git remote -v && gh repo view --json name,visibility,defaultBranchRef`

Expected: repository visibility matches the owner's current choice, default branch is `main`, and all local commits are pushed.

### Task 6: Add initial typed agent contracts

**Files:**
- Create: `src/research_report_agent/contracts.py`
- Create: `tests/test_contracts.py`
- Modify: `src/research_report_agent/__init__.py`

**Interfaces:**
- Consumes: the JSON contracts in `docs/spec/design.md`
- Produces: Pydantic models for plans, worker results, critic reviews, guardrail reviews, and reports

- [x] **Step 1: Write contract tests**

Create tests that validate plan size, dependency cycles, source references, guardrail verdicts, and citation maps.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_contracts.py -v`

Expected: import failure for `research_report_agent.contracts`.

- [x] **Step 3: Implement Pydantic contracts**

Implement typed models and semantic validators.

- [x] **Step 4: Run full quality suite**

Run: `ruff format --check . && ruff check . && pytest`

Expected: all checks pass.

- [x] **Step 5: Commit**

Run: `git add src/research_report_agent tests/test_contracts.py && git commit -m "feat: add typed agent contracts"`
