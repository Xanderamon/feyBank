# feyBank

A homelab infrastructure stack built around a fictional fintech payment API. The application is a pretext; the infrastructure is the subject.

The endgame: Alertmanager detects an anomaly → Python worker collects logs and queries a local LLM → LLM returns a diagnosis and a fix → the worker executes the corresponding Ansible playbook. The system self-heals without human intervention.

---

## Hardware

```
┌──────────────────────────────────┐   SSH + Tailscale   ┌─────────────────────────────────────┐
│  flex  (control node)            │ ──────────────────► │  Menhir  (server)                   │
│                                  │                      │                                     │
│  Intel i3 · 8GB RAM              │                      │  AMD 6-core · 16GB RAM · RTX 3070   │
│  Debian 12 (WSL2)                │                      │  AlmaLinux (WSL2 → bare metal TBD) │
│                                  │                      │                                     │
│  VS Code · Git · Ansible         │                      │  Docker · k3s · Prometheus          │
│  SSH client · Terraform          │                      │  Loki · Ollama · Grafana            │
└──────────────────────────────────┘                      └─────────────────────────────────────┘
```

No public internet exposure. Both nodes on the same Tailscale tailnet.

---

## Application Stack

feyBank simulates a payment API. The domain exists to produce coherent, realistic logs and metrics — not as an engineering subject in itself.

**PostgreSQL — two tables:**

| Table | Key columns |
|---|---|
| accounts | id, owner_name, balance, currency, status |
| transactions | id, from_account, to_account, amount, status, created_at, error_code |

**Redis — two roles:**

| Role | Mechanism | Failure signal |
|---|---|---|
| Session tokens | TTL-based keys | Redis restart → session loss |
| Balance cache | Read-through | Redis failure → latency spike on balance queries |

Redis is load-bearing. Its failure is expected to produce an observable signal, not a silent degradation.

**FastAPI endpoints:**

`POST /accounts` · `GET /accounts/{id}/balance` · `POST /transactions` · `GET /transactions/{id}` · `GET /health` · `GET /metrics` · `POST /ai/explain-error` *(Layer 6+)*

---

## Load Generator

A permanent fifth component. Runs as a standalone Docker container, external to k3s and external to the application. Never removed.

**Rationale for external placement:** the load generator is the continuous observer. It must survive the failures it is supposed to detect. A generator running inside k3s cannot reliably signal that k3s is degraded.

**Normal mode:** ~60 req/min, continuous.

| Request type | Share | App behavior |
|---|---|---|
| Successful transaction | 85% | 2xx · balance updated · Redis cache written |
| Business failure (insufficient balance) | 10% | 4xx · WARN log · error_code set |
| Malformed request | 5% | 4xx · ERROR log |

**Burst mode:** ~500 req/min for a configurable duration. Triggered via environment variable. Used for HPA testing (Layer 5) and pre-chaos baselines (Layer 7).

Request rate is configurable via environment variable — no code change required.

---

## Infrastructure Stack

| Layer | Technology | Purpose |
|---|---|---|
| Containers | Docker · Docker Compose | Local runtime — Layer 0 |
| Reverse proxy | Nginx | TLS termination · routing — Layer 1 |
| Observability | Prometheus · Grafana · Alertmanager | Metrics · dashboards · alerts — Layer 2 |
| CI/CD | GitHub Actions · Trivy | Build · scan · deploy — Layer 3 |
| Configuration | Ansible | Full environment reproducibility — Layer 4 |
| Orchestration | k3s · Helm | Production-like workload management — Layer 5 |
| AI inference | Ollama · Llama 3.1 8B (Q4) · RTX 3070 | Local LLM for incident diagnosis — Layer 6 |
| Log aggregation | Loki · Promtail | Log pipeline for self-healing trigger — Layer 7 |
| IaC | Terraform | Cloud lift-and-shift — Layer 8 |

---

## How to Run

**Prerequisites:** Docker + Docker Compose on the server. Tailscale active on both nodes.

```bash
git clone git@github.com:<user>/feyBank.git
cd feyBank
docker compose up -d
```

Verify the application is live:

```bash
curl http://menhir:8000/health
# {"status": "ok"}

curl http://menhir:8000/metrics
# Prometheus text format
```

Verify the load generator is producing traffic:

```bash
docker compose logs -f load-generator
```

---

## Repository Structure

```
feyBank/
├── app/                    # FastAPI application
├── services/
│   ├── load-generator/     # Synthetic traffic generator
│   └── ai-assistant/       # Python worker for LLM-driven self-healing
├── docker/                 # Docker Compose and container configuration
├── kubernetes/             # k8s manifests, Helm charts, HPA
├── ansible/                # Provisioning playbooks and roles
├── terraform/              # Infrastructure as Code
├── monitoring/             # Prometheus, Grafana, Alertmanager config
├── logging/                # Loki, Promtail config
├── github-actions/         # CI/CD pipeline definitions
└── runbooks/               # Incident documentation
```

Each layer produces `README.md`, `ARCHITECTURE.md`, and `RUNBOOK.md` before it is considered complete. Layer-specific documentation lives alongside the relevant code.
