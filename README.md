# Therapeutic Program Architect

Runs a complete therapeutic drug-development program for any disease — end to end, scientist in the loop.

A specialist agent profile and its companion skills for **Claude Science**.
Runs an end-to-end, human-in-the-loop therapeutic drug program for any disease: unmet need -> targets/modality -> AI/ML design -> scientific/regulatory/commercial strategy -> deliverables.

## What's in this repository

```
agent/
  profile.json         # picker metadata (name, description, access)
  system_prompt.md     # the agent's identity / opening system prompt
  agent_manifest.json  # (legacy) manifest from the original release
skills/                # 8 skills, each with SKILL.md, kernel.py, and any assets
install.py             # one-shot, idempotent installer (recommended)
deploy_agent.py        # (legacy) original deploy script from the first release
```

### Skills bundled

- **agentic-campaign-manuscript**
- **antigen-epitope-pipeline**
- **drug-program-orchestration**
- **omics-target-mining**
- **patient-centered-market-and-survey**
- **scientific-poster**
- **synthetic-peer-review**
- **systematic-review-orchestration**

## Install it in Claude Science

### Easiest — paste one prompt to your Claude Science agent

> Please install the Therapeutic Program Architect from this GitHub repo:
> https://github.com/ruthannepai-tech/therapeutic-program-architect
> Clone or download it, then run `install.py` from the repo root in the repl tool
> with `exec(open("install.py").read())`. It will create and publish the skills and
> create the DRUG_PROGRAM_ARCHITECT agent profile with full access. Then create its environment and
> offer to switch me to it.

When it finishes, **Therapeutic Program Architect** appears in your agent picker.

### One command — if you already have the repo

From the repo root, in the Claude Science **repl** tool:

```python
exec(open("install.py").read())
```

`install.py` publishes every skill under `skills/` (with all their asset files)
and creates the `DRUG_PROGRAM_ARCHITECT` agent profile with full catalog + connector access. It
is **idempotent** — safe to re-run; it updates in place. It finishes by printing
the optional environment setup and the switch command.

### Manual

The skill files and `agent/` files are plain text and fully define everything.
(`deploy_agent.py` from the original release is preserved for reference; the
`install.py` route above is the maintained one.)

## A note on shared skills

Some skills here are shared with other agents I've published, so they're bundled
in each repo that needs them. If you improve one, the same change may be worth
applying wherever it appears:

- `agentic-campaign-manuscript`
- `antigen-epitope-pipeline`
- `omics-target-mining`
- `synthetic-peer-review`
- `systematic-review-orchestration`

## License

MIT — see [LICENSE](LICENSE).
