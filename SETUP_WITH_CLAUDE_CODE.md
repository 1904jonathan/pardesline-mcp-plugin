# Publish this repo with Claude Code

This folder is a **ready-to-publish** Claude Code plugin distribution. It is already a
local git repo with a first commit. You just need to create the public GitHub repo
`1904jonathan/pardesline-mcp-plugin` and push.

## Option A — paste this prompt into Claude Code (run it from THIS folder)

> Open Claude Code with this directory as the workspace, then paste:

```
You are in the local git repo for my PUBLIC Claude Code plugin distribution
(pardesline-mcp-plugin). It contains ONLY non-confidential config + docs + bundled
skills — no platform source code. Do the following, stopping to report if anything looks
off:

1. Confirm there are no secrets staged: search the working tree for `pl_`, `secret`,
   `password`, `DATABASE_URL`, `ANTHROPIC_API_KEY`, private keys. The only API key
   reference allowed is the literal placeholder `pl_your_key_here` and the env-var
   `${PPLINE_API_KEY}`. Abort and tell me if you find anything else.
2. Verify `gh auth status`. If not authenticated, tell me to run `gh auth login` first.
3. Create the PUBLIC GitHub repo and push:
     gh repo create 1904jonathan/pardesline-mcp-plugin --public --source=. --remote=origin \
       --description "ProductPardesLine — 3D-CV & medical-imaging MCP plugin for Claude Code" --push
   If the repo already exists, instead: `git remote add origin
   https://github.com/1904jonathan/pardesline-mcp-plugin.git` then `git push -u origin main`.
4. After pushing, verify the marketplace is reachable: confirm
   `.claude-plugin/marketplace.json` is at the repo root on the default branch, and that
   `plugins/ppline-3dcv/.claude-plugin/plugin.json` exists.
5. Report the final install commands a user should run:
     /plugin marketplace add 1904jonathan/pardesline-mcp-plugin
     /plugin install ppline-3dcv@ppline-3dcv-tools
```

## Option B — manual commands (PowerShell or bash)

```bash
# from inside this folder, with gh authenticated:
gh repo create 1904jonathan/pardesline-mcp-plugin --public --source=. --remote=origin \
  --description "ProductPardesLine — 3D-CV & medical-imaging MCP plugin for Claude Code" --push

# OR, if you created the empty repo on github.com first:
git remote add origin https://github.com/1904jonathan/pardesline-mcp-plugin.git
git branch -M main
git push -u origin main
```

## Verify end-to-end (any machine with Claude Code)

```bash
export PPLINE_API_KEY=pl_your_key_here     # PowerShell: $env:PPLINE_API_KEY="pl_..."
/plugin marketplace add 1904jonathan/pardesline-mcp-plugin
/plugin install ppline-3dcv@ppline-3dcv-tools
/mcp        # ppline-3dcv should show "connected"
```

## Keeping it in sync with the private platform repo

When the bundled skills or the plugin manifest change in the private repo
(`plugins/ppline-3dcv/` + `.claude-plugin/marketplace.json`), re-copy them here, bump the
`version` in both `marketplace.json` and `plugin.json`, commit, and push. The
platform-served `.zip` (`GET /api/mcp/plugin`) and this git repo should stay on the same
version.
