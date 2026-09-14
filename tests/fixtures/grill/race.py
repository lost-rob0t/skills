"""Counter increment used by concurrent job runners."""

import json
from pathlib import Path

STATE = Path("/var/lib/jobs/state.json")


def claim_job(job_id: str) -> bool:
    state = json.loads(STATE.read_text())
    if state["claimed"]:
        return False
    state["claimed"] = True
    state["owner"] = job_id
    STATE.write_text(json.dumps(state))
    return True
