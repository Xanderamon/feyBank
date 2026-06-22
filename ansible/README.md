# ansible/

Provisioning playbooks and roles for the server environment.

Running `ansible-playbook site.yml` on a clean AlmaLinux install reproduces the full environment: users, SSH keys, Docker, firewall, monitoring stack, and the load generator. Roles are separated by concern: `common`, `docker`, `monitoring`, `app`, `ollama`.

Idempotency is verified — running the playbook twice produces no unintended changes.

**Introduced:** Layer 4
