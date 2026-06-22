# github-actions/

CI/CD pipeline definitions for GitHub Actions.

Pipeline: build Docker image → scan with Trivy → deploy to server via SSH. The pipeline fails on critical CVEs — this is non-configurable. Secrets are managed via GitHub Actions Secrets; no credentials appear in code or logs.

End-to-end time from push to deploy targets under 3 minutes.

**Introduced:** Layer 3
