# kubernetes/

Kubernetes manifests and Helm charts for the feyBank application stack.

Covers Deployments, Services, ConfigMaps, Secrets, Ingress, PersistentVolumeClaims, and HPA configuration. Includes a custom feyBank Helm chart configurable via `values.yaml`.

The load generator is not defined here. It runs as a standalone Docker container on the host, external to the cluster by design.

**Introduced:** Layer 5
**Runtime:** k3s on AlmaLinux (WSL2)
