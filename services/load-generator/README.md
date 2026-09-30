# services/load-generator/

Synthetic traffic generator for the feyBank demo application.

This service runs as a standalone Docker container and is intentionally external to k3s and the application stack. It is designed to produce continuous, realistic traffic that exposes failure modes, drives Prometheus/Grafana alerting baselines, and gives chaos tests a live client.

## What the Python script does

The script `load_generator.py` implements an asynchronous traffic generator using `httpx.AsyncClient`.

Key behavior:

- Normal mode generates about `REQUESTS_PER_MINUTE` requests per minute. The default is `60` RPM.
- Burst mode can be enabled with `BURST_MODE=true` and targets `BURST_RPM` requests per minute for `BURST_DURATION_SECONDS` seconds.
- It cycles requests continuously and logs a periodic summary every 30 seconds.
- It targets the application API and health endpoints to simulate realistic external traffic.

## Request distribution

The generator currently uses these request scenarios:

- `success` (80% weight): `GET /api/v1/auth/ok`
- `health` (5% weight): `GET /health`
- `metrics` (5% weight): `GET /metrics`
- `business_failure` (7% weight): `POST /api/v1/auth/ok` with intentionally invalid body data
- `malformed` (3% weight): `POST /api/v1/auth/ok` with malformed JSON

The ratio is designed to approximate the documented traffic profile: mostly successful requests, with some business failures and malformed requests.

## How the script works

- `LoadGenerator` builds a set of `RequestScenario` objects.
- Each scenario includes the HTTP method, target path, selection weight, and an optional payload builder.
- Requests are selected by weighted random choice and dispatched asynchronously.
- Response codes are classified as:
  - 2xx → success
  - 4xx → client error
  - 5xx → server error
- Additional counters track business failure and malformed request scenarios separately.
- Network errors are also captured and logged.

## Environment variables

The service supports the following variables:

- `TARGET_URL` — base URL of the target app (default: `http://app:8000`)
- `API_PREFIX` — API prefix for auth endpoints (default: `/api/v1`)
- `REQUESTS_PER_MINUTE` — normal-mode request rate (default: `60`)
- `BURST_MODE` — enable burst mode (`true|false`, default: `false`)
- `BURST_RPM` — burst request rate when burst mode is enabled (default: `500`)
- `BURST_DURATION_SECONDS` — burst mode duration in seconds (default: `60`)
- `LOG_LEVEL` — Python logging level (default: `INFO`)

## Docker packaging

The service uses a simple container image built from `Dockerfile`.

- `requirements.txt` installs `httpx`.
- `Dockerfile` copies the script into the container and executes `python3 load_generator.py`.

## Running in Docker Compose

The top-level `docker/docker-compose.yml` file already defines the `load-generator` service with:

- `TARGET_URL=http://app:8000`
- `REQUESTS_PER_MINUTE=60`

If you want burst mode, add or override the environment variables:

```yaml
environment:
  TARGET_URL: http://app:8000
  REQUESTS_PER_MINUTE: "60"
  BURST_MODE: "true"
  BURST_RPM: "500"
  BURST_DURATION_SECONDS: "120"
```

## Notes

- The current generator is intentionally lightweight and focuses on external HTTP-level traffic.
- It does not require internal database access or application instrumentation.
- It is meant to stay running during Layer 7 chaos tests and normal baseline monitoring.
