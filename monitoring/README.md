# monitoring/

Configuration for the observability stack: Prometheus, Grafana, and Alertmanager.

Prometheus scrapes `/metrics` from the FastAPI application. Grafana dashboards cover request rate, error rate, CPU, RAM, and GPU metrics (RTX 3070 via nvidia-smi exporter). Alert thresholds are calibrated against the load generator's normal-mode baseline — not against silence.

**Introduced:** Layer 2
