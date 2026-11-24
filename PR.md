# PR for `agentclientprotocol/registry`

Paste this as the pull request against
[`agentclientprotocol/registry`](https://github.com/agentclientprotocol/registry),
after `./apply.sh` has put `agentty/` into your checkout.

**Title:** `Add agentty`

---

Adds [agentty](https://agentty.org) — a terminal-native coding agent that also
ships a full ACP agent (`agentty acp`), so it can be driven from any
ACP-compatible editor.

**Distribution:** raw per-platform GitHub release binaries, pinned to `v0.9.62`
with SHA-256. The Linux builds are fully static (musl), so the same asset is
declared under both the plain and the `-musl` platform key.

| platform | asset |
|----------|-------|
| `darwin-aarch64` | `agentty-macos-arm64` |
| `darwin-x86_64` | `agentty-macos-x86_64` |
| `linux-aarch64`, `linux-aarch64-musl` | `agentty-linux-aarch64` |
| `linux-x86_64`, `linux-x86_64-musl` | `agentty-linux-x86_64` |
| `windows-x86_64` | `agentty-windows-x86_64.exe` |

**Auth:** the ACP `initialize` handshake advertises the `agentty-login` auth
method whenever no credentials are present, so a fresh install is usable.
Verified against a clean `$HOME` with the client shape
`verify_agents.py --auth-check` uses:

```
→ initialize {clientCapabilities: {terminal: true, _meta: {"terminal-auth": true}}}
← authMethods: [{id: "agentty-login", name: "Sign in to agentty",
                  type: "terminal", args: ["login"]}]
← agentInfo: {name: "agentty", version: "0.9.62"}, protocolVersion: 1
```

A client that advertises no auth capability at all still gets one method
(`agentty-login`, agent-managed), so the check passes either way.

**License:** MIT — https://github.com/agentty-org/agentty/blob/master/LICENSE

**Note:** supersedes #543, which was closed without review. That entry omitted
the now-required `license_url`, pointed `repository`/assets at a personal fork
instead of the upstream release stream, and pinned a version from before the
ACP work landed.

---

## Checklist before opening

- [ ] `uv run --with jsonschema .github/workflows/build_registry.py` passes
- [ ] `python3 .github/workflows/verify_agents.py --auth-check --agent agentty` passes
- [ ] the referenced `v0.9.62` release exists with those exact asset names
- [ ] the entry is at `agentty/`, not `agents/agentty/`
