# docker/

Docker Compose configuration for the full application stack.

Defines five services: FastAPI, PostgreSQL, Redis, the load generator, and the database seeder (init only). All services share a single bridge network. Only the FastAPI service is exposed to the host.

PostgreSQL data is persisted via a named volume. Environment variables are injected via `.env` — not committed.

**Introduced:** Layer 0
**Superseded by:** `kubernetes/` in Layer 5 for production workloads. This configuration is retained as the local development runtime.
