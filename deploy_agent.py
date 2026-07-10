"""
deploy_agent.py — recreate the Therapeutic Program Architect profile in a Claude Science workspace.

Run the body of this from a Claude Science `repl` cell (where the `host` object is available).
It is NOT a standalone script — `host.agents.*` only exists inside a Claude Science session.
See the `customize` skill for the full host.agents / host.skills SDK reference.

Prereq: publish the skill first (see README step 1) so the profile has it in the catalog.
"""

import json


def deploy(host, manifest_path="agent/agent_manifest.json", switch=False):
    m = json.load(open(manifest_path))

    # Create the profile with full catalog access (unrestricted => every connector too).
    # If a profile with this name already exists, update its fields instead of recreating.
    existing = {a["name"] for a in host.agents.list()}
    if m["name"] in existing:
        host.agents.update(m["name"], {
            "display_name": m["display_name"],
            "description": m["description"],
            "system_prompt": m["system_prompt"],
            "unrestricted": True,
        })
        action = "updated"
    else:
        host.agents.create(m["name"], m["display_name"], m["description"],
                           system_prompt=m["system_prompt"])
        action = "created"

    # An unrestricted profile already reaches every connector the workspace has, so we do not
    # attach connectors one-by-one. The manifest's connector list documents what the pipeline
    # expects; verify your workspace has them authorized in the Connectors panel.
    prof = [a for a in host.agents.list() if a["name"] == m["name"]][0]
    have = set(prof.get("connectors") or [])
    want = set(m.get("connectors") or [])
    missing = sorted(want - have)

    result = {"action": action, "name": m["name"],
              "display_name": prof.get("displayName"),
              "unrestricted": prof.get("unrestricted"),
              "connectors_present": len(have),
              "connectors_expected_missing": missing}

    if switch:
        host.agents.switch(m["name"])  # user approves a card; takes effect next message

    return result


# In a Claude Science repl cell:
#   from deploy_agent import deploy
#   print(deploy(host, switch=True))
