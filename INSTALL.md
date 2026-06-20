# Installation

## Recommended: Codex plugin install

From the repository root:

```sh
./install.sh
```

This script runs:

```sh
codex plugin marketplace add "$PWD"
codex plugin add codex-bmad-planning-orchestrator@codex-bmad-skills
```

Use this path when you want Codex to install the whole BMAD bundle as a plugin with its shared references and scripts intact.

## Manual plugin install

```sh
codex plugin marketplace add /absolute/path/to/codex-bmad-skills
codex plugin add codex-bmad-planning-orchestrator@codex-bmad-skills
```

## Skills-only install

```sh
./scripts/install-skills.sh
```

This copies the individual `bmad-*` skills into `${CODEX_HOME:-$HOME/.codex}/skills` and copies shared resources into `${CODEX_HOME:-$HOME/.codex}/skills/_bmad-shared`.

Use this only if you specifically need plain skill folders instead of a Codex plugin.

## Uninstall

Plugin install:

```sh
./uninstall.sh
```

Skills-only install:

```sh
./scripts/uninstall-skills.sh --yes
```
