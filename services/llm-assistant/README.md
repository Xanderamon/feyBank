# services/llm-assistant/

Python worker that drives the self-healing pipeline.

Receives Alertmanager webhooks → collects recent logs from Loki → submits context to Ollama → parses the response → executes the appropriate Ansible playbook. Sends incident summary notifications to Telegram or Discord.

LLM output is non-deterministic. This service validates and sanitizes all model responses before passing them to Ansible.

**Introduced:** Layer 7
**Depends on:** Loki (Layer 7), Ollama (Layer 6), Ansible (Layer 4)
