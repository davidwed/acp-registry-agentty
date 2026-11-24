#!/usr/bin/env python3
"""Validate the agentty registry entry against the rules the registry CI enforces.

Mirrors REQUIRED_FIELDS / VALID_PLATFORMS / archive and icon checks from
agentclientprotocol/registry:.github/workflows/build_registry.py. Stdlib only —
no jsonschema, no uv, no network unless --check-urls is passed.

    python3 validate.py                 # offline checks
    python3 validate.py --check-urls    # + HTTP 200 on every archive URL
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
ENTRY = HERE / "agentty"

REQUIRED_FIELDS = {"id", "name", "version", "description", "license_url", "distribution"}
VALID_DISTRIBUTION_TYPES = {"binary", "npx", "uvx"}
VALID_PLATFORMS = {
    "darwin-aarch64",
    "darwin-x86_64",
    "linux-aarch64",
    "linux-aarch64-musl",
    "linux-x86_64",
    "linux-x86_64-musl",
    "windows-aarch64",
    "windows-x86_64",
}
REQUIRED_OS_FAMILIES = {"darwin", "linux", "windows"}
REJECTED_EXTENSIONS = (".dmg", ".pkg", ".deb", ".rpm", ".msi", ".appimage")
ALLOWED_FILL_STROKE = {"currentcolor", "none", "inherit"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def check_top_level(data: dict) -> None:
    for field in sorted(REQUIRED_FIELDS - data.keys()):
        err(f"missing required field '{field}'")
    agent_id = data.get("id", "")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", agent_id):
        err(f"id '{agent_id}' must be lowercase letters/digits/hyphens, starting with a letter")
    if agent_id and ENTRY.name != agent_id:
        err(f"directory '{ENTRY.name}' must match id '{agent_id}'")
    version = data.get("version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        err(f"version '{version}' must be plain semver x.y.z")
    for field in ("repository", "website"):
        if field in data and not str(data[field]).startswith("https://"):
            err(f"{field} must be an https URL")
    if "license_url" in data and not str(data["license_url"]).startswith("https://"):
        err("license_url must be an https URL")


def check_binary(version: str, binary: dict) -> None:
    if not binary:
        err("distribution.binary is empty")
        return
    for platform, target in sorted(binary.items()):
        if platform not in VALID_PLATFORMS:
            err(f"{platform}: not a valid platform key")
        archive = target.get("archive", "")
        cmd = target.get("cmd", "")
        if not archive:
            err(f"{platform}: missing 'archive'")
        if not cmd:
            err(f"{platform}: missing 'cmd'")
        if "/latest/" in archive:
            err(f"{platform}: archive URL must not use /latest/")
        if version and version not in archive:
            err(f"{platform}: archive URL does not contain version {version}")
        if archive.lower().endswith(REJECTED_EXTENSIONS):
            err(f"{platform}: installer archives are rejected ({archive.rsplit('.', 1)[-1]})")
        digest = target.get("sha256")
        if digest is None:
            warn(f"{platform}: no sha256 pinned")
        elif not re.fullmatch(r"[0-9a-f]{64}", digest):
            err(f"{platform}: sha256 must be 64 lowercase hex chars")
        if not isinstance(target.get("args", []), list):
            err(f"{platform}: args must be a list")
    present = {key.split("-")[0] for key in binary}
    for family in sorted(REQUIRED_OS_FAMILIES - present):
        warn(f"no {family} target (allowed, but the review will ask)")


def check_distribution(data: dict) -> None:
    distribution = data.get("distribution") or {}
    kinds = set(distribution) & VALID_DISTRIBUTION_TYPES
    if not kinds:
        err("distribution needs at least one of binary/npx/uvx")
    if "binary" in kinds:
        check_binary(str(data.get("version", "")), distribution["binary"] or {})
    for kind in ("npx", "uvx"):
        if kind in distribution and not distribution[kind].get("package"):
            err(f"distribution.{kind}: missing 'package'")
    if not data.get("repository") and "binary" in kinds:
        warn("no repository field — binary version bumps would need manual PRs")


def check_icon() -> None:
    icon = ENTRY / "icon.svg"
    if not icon.is_file():
        err("agentty/icon.svg is missing")
        return
    text = icon.read_text(encoding="utf-8")
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as exc:
        err(f"icon.svg is not parseable XML: {exc}")
        return

    width = root.get("width", "")
    height = root.get("height", "")
    if width and height:
        if width.strip("px") != "16" or height.strip("px") != "16":
            err(f"icon must be 16x16, got {width}x{height}")
    else:
        view_box = root.get("viewBox", "")
        parts = view_box.replace(",", " ").split()
        if len(parts) != 4 or parts[2:] != ["16", "16"]:
            err(f"icon needs width/height 16 or viewBox '0 0 16 16', got {view_box!r}")

    has_current_color = False
    for elem in root.iter():
        for attr in ("fill", "stroke"):
            value = elem.get(attr)
            if value is None:
                continue
            if value.strip().lower() == "currentcolor":
                has_current_color = True
            elif value.strip().lower() not in ALLOWED_FILL_STROKE:
                err(f"icon has hardcoded {attr}: {value!r} (only currentColor/none/inherit)")
    if not has_current_color:
        err("icon never uses currentColor — it will not follow the light/dark theme")
    if "#" in text:
        err("icon contains a hardcoded colour literal (#...)")


def check_urls(binary: dict) -> None:
    print("\nURL accessibility")
    for platform, target in sorted(binary.items()):
        url = target.get("archive", "")
        if not url:
            continue
        request = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        except Exception as exc:  # noqa: BLE001 - report, never crash
            print(f"  {platform:<22} ERROR {exc}")
            err(f"{platform}: archive URL not reachable ({exc})")
            continue
        marker = "ok" if status == 200 else "FAIL"
        print(f"  {platform:<22} {status} {marker}")
        if status != 200:
            err(f"{platform}: archive URL returned HTTP {status}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-urls",
        action="store_true",
        help="also HEAD every archive URL (network)",
    )
    args = parser.parse_args()

    manifest = ENTRY / "agent.json"
    if not manifest.is_file():
        print(f"error: {manifest} not found", file=sys.stderr)
        return 2
    data = json.loads(manifest.read_text(encoding="utf-8"))

    check_top_level(data)
    check_distribution(data)
    check_icon()

    binary = (data.get("distribution") or {}).get("binary") or {}
    print(f"{data.get('id')} {data.get('version')} — {len(binary)} platform target(s)")
    for platform, target in sorted(binary.items()):
        print(f"  {platform:<22} {target.get('sha256', '(no sha256)')[:16]}…")

    if args.check_urls:
        check_urls(binary)

    for warning in warnings:
        print(f"warn: {warning}")
    for problem in errors:
        print(f"FAIL: {problem}")
    if errors:
        print(f"\n{len(errors)} error(s)")
        return 1
    print("\nOK — entry matches the registry's rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
