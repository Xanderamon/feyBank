# logging/

Configuration for the log aggregation pipeline: Loki and Promtail.

Promtail collects logs from all running services and forwards them to Loki. The llm-assistant queries Loki directly when an alert fires to retrieve the relevant log window for LLM analysis.

**Introduced:** Layer 7
**Depends on:** observability stack (Layer 2)
