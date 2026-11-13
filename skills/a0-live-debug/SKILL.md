---
name: a0-live-debug
description: a0, agent-zero, docker, live-debug, scheduler, tasks, csrf, chats
compatibility: any environment with docker access to a running Agent Zero container
---

# Agent Zero Live Container Debug

## Goal

Inspect and debug a running, dockerized Agent Zero runtime without touching the
host outside the container.

## Input

A running A0 container (default name `agent-zero`, image `a0-symbolics:local`).
All commands run inside the container via `docker exec`; the runtime root is
`/a0`.

## Output

Concrete diagnosis of backend/UI/scheduler problems plus verified fixes.

## Layout (inside container)

| Path | Contents |
| --- | --- |
| `/a0/usr/scheduler/tasks.json` | Scheduler task list (`state`, `last_result` carries run errors) |
| `/a0/usr/chats/<ctx>/messages/N.txt` | Per-context chat turns; higher N = newer |
| `/a0/usr/projects/<slug>/` | Projects; slug is the **folder name**, `.a0proj/project.json` holds the `title` |
| `/a0/tmp/` | Runtime caches (memory, playwright) |
| `/a0/webui/` | Served WebUI source (compare md5 against repo when UI misbehaves) |

## Workflow

1. Identify container and uptime: `docker ps --format '{{.Names}}\t{{.Status}}'`.
2. Read scheduler state first; `last_result` records exact run errors:
   `docker exec agent-zero python3 -c "import json;d=json.load(open('/a0/usr/scheduler/tasks.json'));[print(t['name'],t['state'],t.get('last_result')) for t in d['tasks']]"`
3. Read worker chat tails for recent agent-side context:
   `docker exec agent-zero sh -c 'cat /a0/usr/chats/<id>/messages/$(ls /a0/usr/chats/<id>/messages | sort -n | tail -1).txt'`
4. Check container logs, filtering reaped-pid noise:
   `docker logs agent-zero --since 30m 2>&1 | grep -viE "reaped unknown pid" | tail -50`
5. Smoke-test APIs from inside the container. CSRF needs a **cookie jar plus
   Origin header** (login-disabled mode rejects `Origin: None`):
   ```sh
   docker exec agent-zero sh -c '
     curl -s -c /tmp/cj http://localhost:80/api/csrf_token \
       -H "Origin: http://localhost:5080" > /tmp/ct.json
     TOKEN=$(python3 -c "import json;print(json.load(open(\"/tmp/ct.json\"))[\"token\"])")
     curl -s -X POST http://localhost:80/api/<endpoint> \
       -H "Content-Type: application/json" -H "Origin: http://localhost:5080" \
       -H "X-CSRF-Token: $TOKEN" -b /tmp/cj -d "{\"timezone\":\"America/New_York\"}"'
   ```
6. Endpoints are `/api/<name>`; bare `/<name>` returns 405. GET on POST-only
   endpoints returns 405 - always use POST.
7. Fix persisted data directly only after root-cause confirmation, then re-run
   the failing operation through the API to verify.

## Known Failure Modes

- **Task runs fail with `FileNotFoundError ... /usr/projects/<Name>/.a0proj/project.json`**
  - Task stores a display **title** (`Hackmode`) instead of the folder **slug**
    (`hackmode`); Linux is case-sensitive. Fix `project_name` (and
  `project.name`) in `tasks.json` to the folder slug. Listings succeed because
  serialization never touches disk - only `activate_project` fails at run time.
- **`CSRF token missing or invalid` via curl** - missing cookie jar or Origin
  header; see step 5. `Origin None not allowed when login is disabled` means
  the Origin header was absent.
- **UI shows no tasks but tasks.json has them** - check the browser console and
  `ALLOWED_ORIGINS`; the fetch path is `/scheduler_tasks_list` POST via
  `webui/components/modals/scheduler/scheduler-store.js`.

## Rules

- Never edit tasks.json while a task is `running`; set state to `idle` only
  after confirming the run actually failed.
- Prefer reproducing through the real API path over reading files; file reads
  prove state, API calls prove behavior.
- Do not restart the container as a first move; read state first.
- Mask tokens/secrets when pasting logs or chat excerpts.

## Verification

```sh
docker exec agent-zero python3 -c "import json;print([t['state'] for t in json.load(open('/a0/usr/scheduler/tasks.json'))['tasks']])"
docker logs agent-zero --since 5m 2>&1 | grep -ci traceback
```
