# agentty — ACP Registry entry (ready to submit)

This repository is a **clone-and-go package for the ACP Registry submission of
[agentty](https://agentty.org)**. It exists so the upstream owner can open the
registry PR in about two minutes, without touching agentty's build or docs.

The layout mirrors what the registry expects: everything inside `agentty/` is
exactly what belongs at the top level of
[`agentclientprotocol/registry`](https://github.com/agentclientprotocol/registry).

```
agentty/
├── agent.json   # registry manifest (pinned release, sha256 per platform)
└── icon.svg     # 16x16, monochrome, currentColor
```

## Submit (for the upstream owner)

```sh
git clone https://github.com/davidwed/acp-registry-agentty
```

Then:

```sh
# 1. fork https://github.com/agentclientprotocol/registry on GitHub, then:
git clone https://github.com/<you>/registry && cd registry
git checkout -b add-agentty

# 2. drop the entry in (refuses to overwrite an existing agentty/ dir)
/path/to/this/repo/apply.sh "$PWD"

# 3. validate exactly like CI does
uv run --with jsonschema .github/workflows/build_registry.py
python3 .github/workflows/verify_agents.py --auth-check --agent agentty

# 4. commit and open the PR (body: PR.md)
git add agentty && git commit -m "Add agentty"
git push -u origin add-agentty
```

`gh` alternative for steps 1 and 4: `gh repo fork agentclientprotocol/registry
--clone`, then `gh pr create --title "Add agentty" --body-file PR.md`.

## What is pinned

`agent.json` pins `v0.9.62` of `agentty-org/agentty` with SHA-256 per platform.
The Linux builds are fully static (musl), so the same asset is declared under
both the plain and the `-musl` platform key.

| platform | asset |
|----------|-------|
| `darwin-aarch64` | `agentty-macos-arm64` |
| `darwin-x86_64` | `agentty-macos-x86_64` |
| `linux-aarch64`, `linux-aarch64-musl` | `agentty-linux-aarch64` |
| `linux-x86_64`, `linux-x86_64-musl` | `agentty-linux-x86_64` |
| `windows-x86_64` | `agentty-windows-x86_64.exe` |

## After the merge

No further PRs are needed for releases: the registry's hourly cron re-points the
`version` and every `archive` URL at the newest GitHub release and re-reads the
SHA-256 digests. That requires the **asset names above to stay stable** across
releases — they do (`agentty-<os>-<arch>`), which is why no
`custom_agent_sources/agentty.py` resolver is needed.

A PR is only needed again if the platform set, the asset naming, or the
`license_url` changes.

## Keeping this in sync with upstream

`agentty/` is a copy of `docs/acp-registry/` in the agentty repository, which is
the source of truth. After a release that changes the manifest (new platform,
asset rename), refresh it:

```sh
./sync.sh /path/to/agentty-checkout
python3 validate.py --check-urls
```

## Verify without any tooling

```sh
python3 validate.py               # schema rules, offline
python3 validate.py --check-urls  # + HTTP 200 on every archive URL
```

Both scripts are stdlib-only Python 3, no packages required.

## License

The manifest and icon describe agentty and are published under the same MIT
license as [agentty](https://github.com/agentty-org/agentty/blob/master/LICENSE).
