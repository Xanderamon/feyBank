# services/load-generator/

Synthetic traffic generator. Runs as a standalone Docker container, permanently external to k3s.

Produces ~60 req/min in normal mode against the feyBank API with a realistic error distribution: 85% successful transactions, 10% business failures (insufficient balance), 5% malformed requests. Burst mode targets ~500 req/min and is triggered via environment variable.

This is not a test fixture. It is the continuous observer that makes incidents visible. Alertmanager thresholds are calibrated against its normal-mode baseline. It must be running during all chaos tests in Layer 7.

**Introduced:** Layer 0
