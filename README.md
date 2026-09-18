# 🛡️ ConfigSentinel

**AI-Assisted Cloud Configuration Drift Detection & Remediation System**

A B.Tech CSE final-year DevOps project that monitors a Linux/cloud server, detects when its real configuration has "drifted" away from an approved desired state, explains the problem in plain English using an LLM, and lets a human safely fix it with one click — via Ansible, never by letting the AI touch the server directly.

---

## Table of Contents
1. [Abstract](#abstract)
2. [Problem Statement](#problem-statement)
3. [Existing System](#existing-system)
4. [Proposed System](#proposed-system)
5. [Objectives](#objectives)
6. [System Architecture](#system-architecture)
7. [Features](#features)
8. [Technology Stack](#technology-stack)
9. [AI Component](#ai-component)
10. [AWS Architecture](#aws-architecture)
11. [Configuration Drift Detection](#configuration-drift-detection)
12. [Ansible Remediation](#ansible-remediation)
13. [Terraform Infrastructure](#terraform-infrastructure)
14. [CI/CD Pipeline](#cicd-pipeline)
15. [Project Structure](#project-structure)
16. [Installation](#installation)
17. [Environment Variables](#environment-variables)
18. [AWS Setup](#aws-setup)
19. [Local Demo Mode (No AWS Needed)](#local-demo-mode-no-aws-needed)
20. [Testing](#testing)
21. [Screenshots](#screenshots)
22. [Security Notes](#security-notes)
23. [Future Enhancements](#future-enhancements)

---

## Abstract

Cloud servers rarely stay in the state they were originally deployed in. Manual hotfixes, failed deployments, forgotten test changes, or even malicious tampering can silently push a server's real ("actual") configuration away from its approved ("desired") configuration — a phenomenon known as **configuration drift**. Left undetected, drift causes outages, security holes, and compliance failures.

ConfigSentinel is a full-stack cloud platform that continuously (or on-demand) scans a Linux server, compares its actual state against a version-controlled desired-state YAML file, flags every difference as a drift incident, asks a large language model (Claude) to explain *what* changed, *why it matters*, and *how severe* it is, and — only after a human explicitly approves — runs a pre-written Ansible task to fix it. The whole workflow is visible on a live web dashboard.

## Problem Statement

DevOps teams (and students learning DevOps) need a simple way to answer: *"Is my server still configured the way it's supposed to be, and if not, what changed and how do I fix it safely?"* Existing enterprise tools (AWS Config, Chef Automate, Puppet Enterprise) solve this but are heavy, expensive, and hard to understand for someone new to the field. There is no small, transparent, end-to-end teaching project that shows the **full loop**: scan → detect → explain (AI) → approve → fix → verify.

## Existing System

- **Manual auditing**: an engineer SSHes in and checks things by hand — slow, error-prone, not repeatable.
- **AWS Config / AWS Systems Manager**: powerful but proprietary, costly at scale, and its rules engine is not beginner-friendly.
- **Chef/Puppet/Ansible alone**: great at *enforcing* state but typically don't explain drift in human language or provide a dashboard with AI-assisted triage.
- **Generic monitoring (CloudWatch, Nagios)**: tracks metrics like CPU/memory but has no concept of "desired configuration" at all.

## Proposed System

ConfigSentinel combines:
- a **desired-state YAML file** (the single source of truth),
- a **scanner** that reads the real server's packages, services, ports, users, and key config files,
- a **drift engine** that diffs desired vs actual,
- an **AI analyzer** that turns a raw diff into a plain-English explanation with a severity rating,
- a **remediation engine** that runs one of a small set of pre-approved Ansible tasks — only after a human clicks "Remediate",
- and a **React dashboard** that ties it all together with compliance %, incident history, and one-click actions.

## Objectives

1. Detect configuration drift automatically and reliably.
2. Explain drift in language a non-expert can understand.
3. Keep remediation 100% human-approved — no autonomous AI actions on infrastructure.
4. Demonstrate a realistic, minimal, well-documented DevOps + Cloud + AI pipeline suitable for a college viva.
5. Work fully offline/locally in **Demo Mode**, with no AWS account required, while also supporting a real AWS EC2 deployment.

## System Architecture

```
Developer
   │  git push
   ▼
GitHub  ──────────────►  GitHub Actions (CI/CD: test → build → docker → security → deploy)
   │
   ▼
ConfigSentinel (FastAPI backend + React dashboard, containerized with Docker)
   │
   ▼
AWS EC2 (Linux server, provisioned by Terraform)  ◄────  AWS CloudWatch (CPU/memory/status metrics)
   │  SSH (read-only scan commands)
   ▼
Configuration Scanner  (packages, services, ports, users, files)
   │
   ▼
Drift Engine  (Desired State YAML  vs  Actual State)
   │
   ▼
 Drift Detected? ── No ──► Dashboard shows "Compliant"
   │ Yes
   ▼
AI Analysis (Claude API — explanation only, read-only input, text-only output)
   │
   ▼
Dashboard + Alert  (compliance %, severity, recommendation)
   │
   ▼
User Confirmation  ("Remediate" button, explicit confirm=true)
   │
   ▼
Ansible Remediation  (one fixed, reviewed task per drift category)
   │
   ▼
Re-scan  ──►  Compliant
```

## Features

1. **User Login** — JWT-based auth, bcrypt-hashed passwords.
2. **Cloud Server Monitoring** — packages, services, open ports, users, key config files, CPU/memory.
3. **Desired Configuration** — a single, readable YAML file (`backend/demo/desired_state.yaml`).
4. **Drift Detection** — pure, unit-tested comparison logic (`backend/scanner/drift_engine.py`).
5. **AI Analysis** — what changed / why it's a problem / severity / possible cause / recommendation.
6. **Web Dashboard** — compliance %, total scans, drift incidents, critical issues, latest scan, AI analysis, remediation status. Buttons: **Scan Now**, **Analyze with AI**, **Remediate**, **View History**.
7. **Remediation** — Ansible-driven, always requires explicit confirmation.
8. **AWS CloudWatch** — CPU, memory (via agent), instance/system status.
9. **Terraform** — provisions EC2, security group, IAM role, CloudWatch alarm.
10. **CI/CD** — GitHub Actions: test → build → Docker build → security checks → deploy.
11. **Docker** — backend Dockerfile + docker-compose (backend + frontend).
12. **Database** — SQLite (dev) / PostgreSQL (prod) via SQLAlchemy, same code either way.
13. **Security** — env-var secrets, least-privilege IAM, input validation, no hardcoded credentials, mandatory confirmation before remediation, no arbitrary command execution.
14. **Demo Mode** — simulate the entire workflow with zero AWS dependency.

## Technology Stack

| Layer     | Technology |
|-----------|------------|
| Frontend  | React.js, React Router, Axios, HTML/CSS |
| Backend   | Python, FastAPI, REST APIs |
| Cloud     | AWS EC2, AWS IAM, AWS CloudWatch |
| DevOps    | Git, GitHub, GitHub Actions, Docker, Ansible, Terraform |
| Database  | SQLite (dev), PostgreSQL (prod) via SQLAlchemy ORM |
| AI        | Anthropic Claude API (`anthropic` Python SDK) |

## AI Component

The AI is used **only** to explain already-detected drift — never to decide what to scan, never to execute anything.

- **Input**: a structured dict `{category, item_name, expected_value, actual_value}` produced by the drift engine — nothing else. No SSH access, no credentials, no tool access are ever given to the model.
- **Output**: strict JSON with five text fields: `what_changed`, `why_problem`, `severity`, `possible_cause`, `recommendation`.
- **Safety by design, not just prompting**:
  - There is no code path from the AI's text output to a shell command anywhere in the codebase.
  - Remediation (`remediation/ansible_runner.py`) only ever looks at the drift's `category` (one of 5 fixed values) to choose from a small, hardcoded, human-reviewed set of Ansible tags. The AI's `recommendation` text is shown to the user for context but is **never parsed or executed**.
  - Every remediation requires `confirm: true` from an authenticated user, logged with `approved_by`.
  - If `ANTHROPIC_API_KEY` isn't set, the system falls back to a clearly-labeled rule-based explanation so the demo still works — it is never presented as if it came from the AI.

See `backend/ai/analyzer.py` for the full implementation and system prompt.

## AWS Architecture

- **EC2**: the monitored Linux server (Amazon Linux 2, nginx + SSH), provisioned by Terraform.
- **Security Group**: only ports 22 (SSH, for scanning/remediation) and 80 (HTTP, for the monitored nginx) are open.
- **IAM Role**: attached to the instance with a least-privilege policy (`cloudwatch:PutMetricData`, `ec2:DescribeTags` only) — no S3, no admin access.
- **CloudWatch**: CPU utilization metric + alarm out of the box; memory metrics if the CloudWatch Agent is installed (done via Terraform `user_data`).
- **No AWS access keys are ever hardcoded.** boto3/Terraform both read credentials from the environment, an IAM role, or your local AWS CLI profile.

## Configuration Drift Detection

`backend/demo/desired_state.yaml` is the source of truth:

```yaml
packages:
  - nginx
services:
  nginx:
    state: running
ports:
  - 22
  - 80
users:
  - admin
```

`backend/scanner/drift_engine.py::detect_drift()` compares this against the actual state (from SSH scanning or the demo simulator) and returns a list of drift dicts such as:

```json
{"category": "service", "item_name": "nginx", "expected_value": "running", "actual_value": "stopped"}
```

A simple, explainable compliance score (`passed_checks / total_checks * 100`) is computed and shown on the dashboard.

## Ansible Remediation

`ansible/remediation.yml` contains exactly five tagged tasks — one per drift category (`fix_service`, `install_package`, `create_user`, `restore_file`, `review_port`). The backend picks the tag purely from the drift's `category` field and passes `target_item`/`desired_value` as `--extra-vars`. Port drift is **never** auto-remediated (flagged for manual review only), since automatically opening/closing firewall ports is a security-sensitive action.

In **Demo Mode**, no real SSH/Ansible call happens — `backend/demo/simulated_server.py` mutates the in-memory simulated state instead, so the whole loop is safe to run anywhere.

## Terraform Infrastructure

`terraform/main.tf` provisions:
- 1× EC2 instance (Amazon Linux 2, free-tier `t2.micro` by default)
- 1× Security Group (SSH + HTTP only)
- 1× IAM Role + Instance Profile (least privilege, CloudWatch write-only)
- 1× CloudWatch CPU alarm

```bash
cd terraform
terraform init
terraform apply -var="key_name=your-ec2-keypair"
terraform output instance_public_ip   # → put this in backend/.env as EC2_HOST
```

## CI/CD Pipeline

`.github/workflows/ci-cd.yml` runs on every push/PR to `main`:

```
Push → GitHub → Run Tests (pytest) → Build Application (npm build)
     → Docker Build → Security Checks (pip-audit + secret scan) → Deploy
```

The `deploy` job is a placeholder you fill in with your actual target (SSH to EC2, push to ECR, etc.) using GitHub Actions **Secrets** — never plaintext credentials in the workflow file.

## Project Structure

```
ConfigSentinel/
│
├── frontend/                 React application (login, dashboard, history)
│   └── src/
│       ├── api/               axios API client
│       ├── components/        StatCard, IncidentCard
│       ├── pages/              LoginPage, DashboardPage, HistoryPage
│       └── styles/
│
├── backend/
│   ├── app.py                 FastAPI entrypoint
│   ├── config.py               env-based settings
│   ├── routes/                 auth, servers, scans, ai, remediation, dashboard, demo
│   ├── services/                auth_service.py, cloudwatch_service.py
│   ├── scanner/                 ec2_scanner.py (SSH), drift_engine.py
│   ├── ai/                      analyzer.py (Claude integration)
│   ├── remediation/             ansible_runner.py
│   ├── demo/                    simulated_server.py, desired_state.yaml
│   └── database/                db.py, models.py, schemas.py
│
├── terraform/                 main.tf, variables.tf, outputs.tf
├── ansible/                   inventory, remediation.yml
├── docker/                    Dockerfile, Dockerfile.frontend, docker-compose.yml
├── .github/workflows/          ci-cd.yml
├── tests/                      pytest unit tests
├── .env.example
└── README.md
```

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional, for real EC2 mode) Terraform, Ansible, an AWS account

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env      # edit values as needed
uvicorn app:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm start
```

Dashboard available at `http://localhost:3000`.

### Docker (both together)

```bash
cp .env.example .env   # fill in values at repo root
docker compose -f docker/docker-compose.yml up --build
```

## Environment Variables

See `.env.example` for the full list. Key ones:

| Variable | Purpose |
|---|---|
| `DEMO_MODE` | `true` = simulated server, no AWS needed |
| `SECRET_KEY` | JWT signing secret — set a long random value |
| `DATABASE_URL` | `sqlite:///./configsentinel.db` or a `postgresql://...` URL |
| `ANTHROPIC_API_KEY` | Enables real AI analysis (falls back to rule-based text if empty) |
| `EC2_HOST`, `EC2_SSH_USER`, `EC2_SSH_KEY_PATH` | Real EC2 scanning target |
| `AWS_REGION` | For boto3/CloudWatch calls |

**No secret is ever hardcoded in source. `.env` is git-ignored.**

## AWS Setup

1. `aws configure` locally (or attach an IAM role in CI), with least-privilege permissions: `ec2:Describe*`, `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`.
2. Provision infrastructure: `cd terraform && terraform init && terraform apply`.
3. Copy the output `instance_public_ip` into `backend/.env` as `EC2_HOST`.
4. Set `DEMO_MODE=false` and register a non-demo server via the dashboard/API with `is_demo: false`.
5. Update `ansible/inventory` with the same IP and your `.pem` key path.

## Local Demo Mode (No AWS Needed)

This is the recommended way to present the project in a viva:

1. Start the backend with `DEMO_MODE=true` (the default).
2. Log in / register on the dashboard — a demo server is auto-created.
3. Click **Scan Now** → shows 100% compliant.
4. Click one of the **Simulate drift** buttons (e.g. "stop nginx") → a scan runs automatically and shows the incident.
5. Click **Analyze with AI** → see the AI's explanation and severity.
6. Click **Remediate** → confirm → the simulated server is fixed.
7. Click **Scan Now** again → back to 100% compliant.

Use **Reset demo server** any time to start over.

## Testing

```bash
cd backend
pytest ../tests -v
```

Covers: drift detection logic (no-drift, missing package/user/file, stopped service, unexpected open port, compliance scoring), the demo simulator's scenarios and remediation, and the AI analyzer's safe fallback path (runs without any network access, so it's CI-safe).

## Screenshots

_Add screenshots here after running the app locally, e.g.:_
- `docs/screenshots/login.png`
- `docs/screenshots/dashboard-compliant.png`
- `docs/screenshots/dashboard-drift-detected.png`
- `docs/screenshots/ai-analysis.png`
- `docs/screenshots/history.png`

## Security Notes

- Passwords are bcrypt-hashed; sessions use short-lived JWTs.
- All API inputs are validated with Pydantic models.
- The scanner runs only a fixed, hardcoded list of **read-only** shell commands — never user-supplied commands.
- The AI never receives credentials or server access, and its output is never executed.
- Remediation always requires an authenticated user to pass `confirm: true`; every remediation is logged with who approved it.
- IAM policies (Terraform) and AWS calls (boto3) follow least privilege.
- No secrets are committed to source control (`.env`, `*.pem`, `terraform.tfvars` are all git-ignored).

## Future Enhancements

- Scheduled/periodic scanning (e.g. via a cron job or APScheduler) instead of manual "Scan Now" only.
- Slack/email alerting when high-severity drift is detected.
- Multi-server fleet view instead of a single monitored server.
- Role-based access control (admin vs read-only viewer).
- Policy-as-code support (e.g. Open Policy Agent) for more complex desired-state rules.
- Historical compliance trend charts.
