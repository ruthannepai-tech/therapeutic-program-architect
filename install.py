"""
One-shot installer for the Patient Organization Navigator.

Run this from a Claude Science conversation, in the `repl` tool, from the root
of this repository:

    exec(open("install.py").read())

It reads the skill and agent definitions in this repo and installs them into
your Claude Science organization via the customize SDK (host.skills.* /
host.agents.*). It is idempotent — safe to re-run; it updates in place.

Requires: a Claude Science `repl` kernel (the `host` object). The figure
renderers also want a conda env with pandas/numpy/matplotlib/seaborn — the
script prints the one tool call to create it (the agent runs that separately,
since environment creation is a tool, not part of this SDK).
"""

import os, json


def _repo_root():
    # Prefer cwd if it looks like the repo; else the script's own directory.
    for cand in (os.getcwd(), os.path.dirname(os.path.abspath(
            globals().get("__file__", "install.py")))):
        if os.path.isfile(os.path.join(cand, "agent", "profile.json")):
            return cand
    raise RuntimeError(
        "Cannot find repo root. Run this from the repository root "
        "(the folder containing agent/profile.json and skills/).")


_PKGMAP = {"numpy": "numpy", "pandas": "pandas", "matplotlib": "matplotlib",
           "seaborn": "seaborn", "scipy": "scipy", "sklearn": "scikit-learn",
           "PIL": "pillow", "networkx": "networkx", "requests": "requests",
           "yaml": "pyyaml"}


def _env_slug(agent_name):
    return agent_name.lower().replace("_", "-")


def _scan_packages(skills_dir):
    """Third-party packages imported by the bundled kernel.py files."""
    import re
    found = set()
    for base, _, files in os.walk(skills_dir):
        for f in files:
            if f == "kernel.py":
                src = open(os.path.join(base, f)).read()
                for m in re.findall(r'^\s*(?:import|from)\s+([A-Za-z_][\w]*)',
                                     src, re.M):
                    if m in _PKGMAP:
                        found.add(_PKGMAP[m])
    return sorted(found) or ["pandas", "numpy", "matplotlib", "seaborn"]


def _put_file(host, skill, path, content):
    """Create the file, or replace it if it already exists (idempotent)."""
    try:
        host.skills.edit(skill, path, content)          # create (fails if exists)
    except Exception:
        cur = host.skills.read(skill, path)["content"]
        if cur != content:
            host.skills.edit(skill, path, content, old_string=cur)


def install(host):
    root = _repo_root()
    skills_dir = os.path.join(root, "skills")
    skills = sorted(d for d in os.listdir(skills_dir)
                    if os.path.isdir(os.path.join(skills_dir, d)))
    print("Installing %d skills from %s" % (len(skills), root))

    for s in skills:
        sd = os.path.join(skills_dir, s)
        md = open(os.path.join(sd, "SKILL.md")).read()
        _put_file(host, s, "SKILL.md", md)
        kp = os.path.join(sd, "kernel.py")
        if os.path.isfile(kp):
            _put_file(host, s, "kernel.py", open(kp).read())
        host.skills.publish(s, overwrite=True)
        print("  published skill:", s)

    # --- Agent profile ---
    prof = json.load(open(os.path.join(root, "agent", "profile.json")))
    system_prompt = open(os.path.join(root, "agent", "system_prompt.md")).read()
    name = prof["name"]
    exists = any(a["name"] == name for a in host.agents.list())
    if exists:
        host.agents.update(name, {
            "display_name": prof["displayName"],
            "description": prof["description"],
            "system_prompt": system_prompt,
            "unrestricted": prof.get("unrestricted", True),
        })
        print("  updated agent:", name)
    else:
        # Leave skill_names unset => full catalog + all connectors (unrestricted).
        host.agents.create(
            name=name,
            display_name=prof["displayName"],
            description=prof["description"],
            system_prompt=system_prompt,
        )
        print("  created agent:", name, "(full access)")

    env = _env_slug(name)
    pkgs = _scan_packages(skills_dir)
    print("\nDone. The '%s' specialist is now in your agent picker." % prof["displayName"])
    print("\nOptional — create its analysis environment (run as a tool call):")
    print("  manage_environments(mode='create', name='%s'," % env)
    print("      packages=%r, python_version='3.13')" % pkgs)
    print("\nThen switch to it:  host.agents.switch('%s')" % name)
    return name


# Auto-run when exec'd in a repl kernel that has `host`.
if "host" in globals():
    install(host)  # noqa: F821
else:
    print("No `host` found. Run this in the Claude Science `repl` tool:")
    print('    exec(open("install.py").read())')
