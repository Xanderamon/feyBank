# feyBank — ARCHITECTURE.md

## Layer 0: Skeleton

>
>
> Scope: this document describes only the architecture decisions made in Layer 0.
> Each subsequent layer will append or supersede sections as needed.
> Last updated: Layer 0
>
>

---

## 1. Hardware Topology

```
┌─────────────────────────────────┐     SSH (key-based)     ┌─────────────────────────────────────┐
│  CONTROL NODE — Laptop          │ ──────────────────────► │  SERVER — Desktop                   │
│                                 │                         │                                     │
│  Intel i3 · 8GB RAM             │                         │  AMD 6-core · 16GB RAM · RTX 3070   │
│  Debian 12 (WSL2)               │                         │  Alma Linux (WSL2 → bare metal TBD)│
│                                 │                         │                                     │
│  Tools: VS Code · Git           │                         │  Runtime: Docker · k3s (later)      │
│         Ansible · SSH client    │                         │           Prometheus · Loki (later)  │
└─────────────────────────────────┘                         │           Ollama (later)             │
                                                            └─────────────────────────────────────┘
```

**Substrate:** both nodes run WSL2 at Layer 0.
**Bare metal migration:** deferred — triggered only if WSL2 instability blocks Layer 5 progress.

---

## 2. Layer 0 Application Stack

```
┌─────────────────────────────────────────────────────────┐
│  Docker Compose — Alma Linux (WSL2)                    │
│                                                         │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │   FastAPI   │───►│  PostgreSQL  │    │   Redis   │  │
│  │  :8000      │    │  :5432       │    │  :6379    │  │
│  │             │    │              │    │           │  │
│  │ GET /health │    │              │    │           │  │
│  │ GET /metrics│    │              │    │           │  │
│  └─────────────┘    └──────────────┘    └───────────┘  │
│                                                         │
│  Network: docker bridge (internal)                      │
└─────────────────────────────────────────────────────────┘
```

**Source:** pre-existing open-source FastAPI demo app. No application code written from scratch.

**Required endpoints (non-negotiable from day one):**

| Endpoint | Returns | Purpose |
| --- | --- | --- |
| GET /health | {"status": "ok"} | Liveness probe baseline |
| GET /metrics | Prometheus text format | Scraped by Prometheus in Layer 2 |

---

## 3. Access Architecture

### 3.1 Decision: SSH Access to Server (Windows Host)

**Chosen model:** dedicated non-admin SSH user (Option B)

**Rejected alternative:** SSH as Administrator via `administrators_authorized_keys` (Option A)

**Rationale:**

Option A was rejected on architectural grounds, not convenience.
The portfolio explicitly demonstrates security discipline at CI/CD level (Trivy, secrets management, least-privilege in K8s). An Administrator-level SSH entry point on the central server node would be structurally inconsistent with that posture — regardless of lab context.

Option B costs ~20 minutes of one-time setup and produces zero operational overhead on the primary Ansible/Docker/K8s workflow, which operates entirely within Alma Linux (WSL2) and does not route through Windows SSH.

**Configuration:**

```
User:     devops (or sshuser)
Group:    NOT Administrators
Auth:     SSH key-based only (password auth disabled)
Escalation: runas /user:Administrator when Windows-level ops required
SSH path: standard .ssh/authorized_keys
```

**Blast radius analysis:**

| Scenario | Option A | Option B |
| --- | --- | --- |
| SSH key compromised | Full Windows system access | Limited to unprivileged user scope |
| Ansible → Alma Linux | Unaffected (separate path) | Unaffected (separate path) |
| Layer 7 Python worker | Unaffected (internal Linux) | Unaffected (internal Linux) |
| Windows-level ops | Implicit | Explicit escalation via runas |

### 3.2 Ansible SSH (Control → Server, Alma Linux)

Ansible operates via a dedicated Linux user on Alma Linux (WSL2), configured with SSH key authentication.
This is a separate access path from the Windows host SSH described in §3.1.

Details: defined in Layer 4 (Configuration Management).

---

## 4. Known Constraints at Layer 0

| Constraint | Impact | Mitigation |
| --- | --- | --- |
| WSL2 IP changes on Windows reboot | Container and SSH endpoints may shift | /etc/hosts entry or static binding (Layer 1) |
| Alma Linux WSL2: systemd disabled by default | Services relying on systemd (Ollama in Layer 6) will fail | systemd=true in /etc/wsl.conf — required before Layer 6 |
| Docker bridge networking on WSL2 | Container-to-container communication may fail on first attempt | Expected debug — not a blocker |

---

## 5. What This Layer Does Not Include

The following components are explicitly **out of scope for Layer 0** and will be introduced in subsequent layers:

- Reverse proxy / TLS (Layer 1)
- Prometheus, Grafana, Alertmanager (Layer 2)
- CI/CD pipeline (Layer 3)
- Ansible provisioning (Layer 4)
- Kubernetes / k3s (Layer 5)
- Ollama / GPU inference (Layer 6)
- Self-healing automation (Layer 7)
- Terraform / cloud (Layer 8)

---

*Next: `RUNBOOK.md` Layer 0 — document first incident before layer is considered complete.*