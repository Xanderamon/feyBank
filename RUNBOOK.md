# feyBank — RUNBOOK.md

## Layer 0: Skeleton

> Format: Problem → Diagnosis → Fix → Lessons Learned
> Each entry includes a `category` and `symptom_pattern` field for automated matching (Layer 7).

---

### Incident 001 — Docker socket permission denied

**Category:** `environment / permissions`

**Symptom pattern:** `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`

**Problem:**
`docker compose up` fails immediately, before any image pull or build starts.

**Diagnosis:**
The current shell session's user is not (yet) a member of the `docker` group, or the group membership was granted but not yet applied to the active session. Group membership is read at login, not dynamically.

**Fix:**
```bash
groups                      # check if "docker" is listed
newgrp docker                # apply group to current session, no logout needed
# OR, more permanently:
exit                         # close session
ssh -p 2222 alma@menhir      # reconnect — new session picks up group
```

**Lessons Learned:**
Any `usermod -aG <group>` change requires a new login session to take effect. If a command fails with a permission error immediately after adding a user to a group, check session freshness before investigating deeper (e.g. socket permissions, daemon config).

**Generalizes to:** any "permission denied on socket/device" error appearing right after a `usermod -aG` change (not just Docker — same pattern applies to e.g. `dialout`, `video` groups).

---

### Incident 002 — Compose variable substitution reads wrong `.env`

**Category:** `configuration / environment variables`

**Symptom pattern:** `The "<VAR_NAME>" variable is not set. Defaulting to a blank string.`

**Problem:**
`docker compose up` starts, but Postgres healthcheck fails or behaves unexpectedly because `${POSTGRES_USER}` / `${POSTGRES_DB}` resolved to empty strings inside the compose YAML itself (not inside the container).

**Diagnosis:**
Two independent mechanisms exist and were confused:
1. `env_file:` in a service — injects variables **into the container** at runtime.
2. `${VAR}` interpolation directly in the `docker-compose.yml` — resolved by **Compose itself at parse time**, using a `.env` file located in the **directory the command is run from**, not the one referenced by `env_file:`.

The `.env` file existed in the project root, but `docker compose` was invoked from a subdirectory (`docker/`) that had no `.env` of its own.

**Fix:**
```bash
cd docker/
ln -s ../.env .env
docker compose config | grep -A2 healthcheck   # verify substitution before starting anything
```

**Lessons Learned:**
`env_file:` and top-level `${VAR}` substitution in the same compose file have different search paths for `.env`. A missing `.env` in the invocation directory produces silent blank-string defaults, not a hard failure — always verify with `docker compose config` before trusting a fresh `up`.

**Generalizes to:** any compose warning of the form `variable is not set. Defaulting to...` — check working directory relative to `.env`, don't assume `env_file:` covers it.

---

### Incident 003 — Build context missing (undeveloped component)

**Category:** `application / missing artifact`

**Symptom pattern:** `failed to read dockerfile: open Dockerfile: no such file or directory`

**Problem:**
`docker compose up --build` fails to build a specific service; the build context directory exists but is effectively empty (only a README, no Dockerfile or source).

**Diagnosis:**
The compose file declares a `build: context:` pointing at a directory for a custom, project-specific component that had not been implemented yet — not a path typo, but a genuinely missing deliverable.

**Fix (short-term, to unblock other services):**
```bash
docker compose up -d --build <other-services-only, excluding-the-missing-one>
```

**Fix (correct, long-term):**
Implement the missing component (Dockerfile + application code) before considering the layer complete.

**Lessons Learned:**
Distinguish "path/config error" from "component not yet built" before debugging paths — check if the target directory contains only documentation. A compose file can be fully valid and still reference deliverables that don't exist yet; this is a project-completeness gap, not an infrastructure bug.

**Generalizes to:** any `no such file or directory` on a `build context` — first check `ls <context-path>` before assuming a path/typo issue.

---

### Incident 004 — Dockerfile RUN command typo breaks build late

**Category:** `application / Dockerfile syntax`

**Symptom pattern:** `did not complete successfully: exit code: 1` after a long, otherwise-successful `apt-get install` sequence

**Problem:**
Docker build fails only at the very last command of a long `RUN` chain, after package installation appeared to succeed.

**Diagnosis:**
A single flag typo in a chained shell command (`rm -ft` instead of `rm -rf`) causes the final cleanup command to fail. Because the whole `RUN` is one shell invocation joined with `&&`, failure of the last command fails the entire layer — even though every prior command in the chain succeeded.

**Fix:**
Correct the invalid flag in the Dockerfile (`-ft` → `-rf`), then rebuild. Docker's layer cache typically keeps prior steps cached, making the rebuild fast.

**Lessons Learned:**
When a build fails at the tail of a long `&&`-chained `RUN`, don't assume the failure is related to what was installed — check the last command in the chain first; it's often a small syntax/flag error unrelated to the packages themselves.

**Generalizes to:** any Docker build failure with `exit code: 1` at the end of a long `RUN` line — isolate and test the final command in the chain independently before investigating the packages or base image.

---

### Incident 005 — Package structure mismatch (relative imports vs. flat COPY)

**Category:** `application / packaging structure`

**Symptom pattern:** `ModuleNotFoundError: No module named 'app'` (from a run command like `uvicorn app.main:app`) OR `ImportError: attempted relative import with no known parent package` (from a script using relative imports)

**Problem:**
Container builds successfully and starts, but crashes immediately (restart loop for long-running services; immediate non-zero exit for one-shot scripts).

**Diagnosis:**
The application source uses relative imports (e.g. `from .db import ...`), meaning the code expects to live inside an importable package. The Dockerfile's `WORKDIR` + `COPY . .` combination flattens the source directly into the working directory, instead of nesting it under a subdirectory matching the package name. The run command (`module.submodule:object` style, or a script using relative imports) then can't resolve the expected package.

**Fix:**
Adjust the Dockerfile to `COPY` the source into a subdirectory matching the package name (one level of `WORKDIR` above where the package should resolve from), rather than changing the application's import style.

**Lessons Learned:**
When a container using relative imports crashes with `ModuleNotFoundError` or `ImportError: attempted relative import`, check whether the Dockerfile's `COPY`/`WORKDIR` structure matches the package name the run command expects — before touching any application code. This is a packaging problem, not a code bug, and should be fixed at the Dockerfile/compose layer.

**Generalizes to:** any Python service failing on startup with either of the two symptom patterns above — first check `docker compose exec <service> ls` and `pwd` to confirm the on-disk structure matches what the run command expects.

---

### Incident 006 — Unpinned dependency breaks on major version upgrade

**Category:** `application / dependency versioning`

**Symptom pattern:** library raises an error referencing a "new" API concept, decorator, or annotation style the application code doesn't use (e.g. `MappedAnnotationError`, "Annotated Declarative Table form", or similar version-specific ORM/framework terminology)

**Problem:**
A container crashes at import/class-definition time — not at request-handling time — with an error message referencing concepts or requirements that seem unrelated to what the code was actually written to use.

**Diagnosis:**
The failing library (here, SQLAlchemy) is a transitive dependency, pulled in without an explicit version pin in `requirements.txt`. The application code was written against an older major version's API/behavior; `pip install` resolved the latest available major version instead, which introduced breaking behavioral changes (not just new features) affecting code that was previously valid.

**Fix:**
Pin the affected library to the major version range the code was actually written for (e.g. `sqlalchemy>=1.4,<2.0`), rather than modifying application code to match the new major version's API — unless a deliberate migration to the new API is intended.

**Lessons Learned:**
Any dependency not explicitly pinned in `requirements.txt` is a moving target — a rebuild months apart can silently resolve a different major version and break code that hasn't changed at all. Errors that reference unfamiliar terminology from a well-known library (rather than an obvious typo or missing file) are a strong signal to check for an unpinned transitive dependency before assuming the application code itself is wrong.

**Generalizes to:** any "it worked before, now it doesn't, and I didn't touch the code" scenario — check `pip list` / `requirements.txt` for missing version constraints before debugging application logic.

---

### Incident 007 — ORM tables never created (metadata populated after create_all runs)

**Category:** `application / import ordering, ORM initialization`

**Symptom pattern:** `psycopg2.errors.UndefinedTable: relation "<table>" does not exist`, raised from a query against a model class that is clearly defined in the codebase

**Problem:**
A query against an ORM model fails because its underlying table was never created in the database — despite `metadata.create_all(engine)` being present in the codebase and apparently having run without error.

**Diagnosis:**
`create_all()` was called at module import time, in a module (`db.py`) that is a dependency of the model-defining modules rather than the other way around. Because of that import direction, `create_all()` always executes before the ORM model classes are defined and registered onto the shared `metadata` object — so at the moment `create_all()` runs, there is nothing yet to create. No error is raised at that point; the call simply does nothing, silently.

**Fix:**
Explicitly call `metadata.create_all(engine)` again, later, after the model modules have been imported (and thus registered) — e.g. at the start of any script or service entrypoint that needs the tables to exist. `create_all()` is idempotent and safe to call more than once.

**Lessons Learned:**
An ORM's `create_all()` (or equivalent schema-sync call) only creates tables for models that have been imported and registered by the time it runs — not all models that exist in the codebase. If `create_all()` lives in a low-level module that model modules depend on (rather than the reverse), it will structurally always run too early. This is easy to miss because it fails silently (no tables, no error) until something actually queries the missing table.

**Open follow-up (not yet resolved):** the FastAPI `app` process has the same latent exposure — it never imports the model modules directly, so its tables may also not exist yet. This hasn't surfaced because no implemented endpoint queries the database yet. Expect this same symptom pattern when `POST /accounts` and similar endpoints are implemented, unless addressed first.

**Generalizes to:** any "table doesn't exist despite `create_all()` being called somewhere in the code" — check whether model class definitions are guaranteed to execute *before* the `create_all()` call, not just present anywhere in the import graph.

---

### Incident 008 — Custom `metadata` injection via `declared_attr` silently ignored

**Category:** `application / ORM declarative configuration`

**Symptom pattern:** `UndefinedTable` persists even after calling `create_all()` at the correct point in the import order (i.e. after model classes are imported) — the fix for "import ordering" (Incident 007) does not resolve the issue.

**Problem:**
Explicitly re-invoking `create_all()` after importing all model classes still does not create any tables, and raises no error — implying `create_all()` believes there is nothing to create.

**Diagnosis:**
The declarative base class overrides `metadata` via `@declared_attr`, intending to make all mapped classes share one specific `MetaData` instance (imported from a lower-level module). `@declared_attr` is designed for evaluation on *subclasses* of a declarative base, not necessarily on the base class's own `metadata` attribute during its own construction — this override may silently fail to apply, causing SQLAlchemy to fall back to an internally-created default `MetaData()`, invisible to the object being explicitly imported and passed to `create_all()` elsewhere.

**Fix:**
Do not rely on importing the "intended" shared `metadata` object from a separate module. Import the declarative `Base` class instead, and call `Base.metadata.create_all(engine)` — this is always the actual metadata object associated with the mapped classes, regardless of how it was assigned internally.

**Lessons Learned:**
When a custom object is "injected" into a class via an unusual or non-standard use of a framework mechanism (here: `declared_attr` for `metadata`, a non-typical use case), don't assume the injection succeeded just because no error was raised. Silent no-ops (as opposed to loud failures) are the most dangerous category of bug precisely because nothing signals that the assumption was wrong. When in doubt, query the framework's own authoritative object (`Base.metadata`) instead of a hand-wired reference to what you believe that object should be.

**Generalizes to:** any case where a "shared singleton" object is imported from one place and passed into a framework call (e.g. `create_all`, `Base.query`, a registry), while the actual registration seems to happen "somewhere else" (declarative class bodies, decorators, metaclasses) — verify the two are actually the same object before trusting silent success.

---

### Incident 009 — passlib/bcrypt version incompatibility (unpinned dependency)

**Category:** `application / dependency versioning`

**Symptom pattern:** `AttributeError: module 'bcrypt' has no attribute '__about__'` followed by `ValueError: password cannot be longer than 72 bytes` — the error appears to be about password length, but occurs during a library's internal self-test, not from the actual password being hashed.

**Problem:**
Password hashing fails with an error that superficially suggests the input password is too long, even when it clearly isn't (e.g. a 12-character test password).

**Diagnosis:**
`passlib` probes the installed `bcrypt` library's version via an internal attribute (`bcrypt.__about__.__version__`) to select compatible behavior. Newer major versions of `bcrypt` removed that attribute. When version detection fails, passlib falls back to running an internal diagnostic ("wrap bug detection") using a hardcoded test string — and it is *that* internal test hash, not the caller's actual password, which trips the length-related `ValueError` under the newer bcrypt version's stricter behavior. `bcrypt` was pulled in without a version pin, so a new major version was installed silently.

**Fix:**
Pin `bcrypt<4.0` in `requirements.txt` (alongside the existing `passlib[bcrypt]` declaration), rather than modifying the password-hashing code — the error is not about actual input, so no application logic needs to change.

**Lessons Learned:**
Same root pattern as Incident 006: unpinned transitive dependencies silently resolve to newer major versions, which can break glue-libraries (like passlib) that assume specific internal APIs of what they wrap. A second signal worth remembering here: error messages from a lower-level self-test can look identical in shape to an error about *your* input — check whether the failing value in the traceback is actually the data you passed in, or a hardcoded value belonging to the library's own internals, before assuming the input is the problem.

**Generalizes to:** any error suggesting your input is invalid, when the input demonstrably isn't (length, format, type) — check if the failure originates from a library-internal self-test/probe rather than from processing the actual argument you passed.

---

### Incident 010 — Divergent images across services after partial rebuilds

**Category:** `operations / build process`

**Symptom pattern:** the same dependency fix appears to work in one service (verified via logs or direct testing) but the identical error persists when testing the same code path in a different service sharing the same `requirements.txt` / build context

**Problem:**
A dependency fix (version pin) is confirmed working in one container, but a sibling service using the same source and requirements file still exhibits the original bug.

**Diagnosis:**
`docker compose build <service>` / `up --build <service>` only rebuilds the named service(s). If a requirements change was made and only one service was rebuilt to verify the fix, other services sharing the same Dockerfile/context remain on the older image — with the old, unpinned dependency version still installed — until explicitly rebuilt themselves.

**Fix:**
Run `docker compose up -d --build` without naming a specific service, to rebuild every service with a `build:` directive, after any change to shared source or requirements files. Verify via `docker compose exec <service> pip freeze | grep <package>` on *each* affected service, not just the one initially tested.

**Lessons Learned:**
A fix confirmed in one container is not confirmed project-wide. When multiple services share a build context or requirements file, always rebuild and re-verify all of them together after a dependency change — testing only the service you happen to be iterating on can create a false sense of resolution while a sibling service silently still carries the bug.

**Generalizes to:** any "it works here but not there" report between two services/containers that are supposed to be built from the same source — check whether both were actually rebuilt after the fix, before investigating the code itself again.