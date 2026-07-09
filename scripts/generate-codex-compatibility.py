#!/usr/bin/env python3
"""Generate Codex's flat skill layout from the upstream Claude manifest."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
OUTPUT = ROOT / "plugins" / "real-engineering-skills" / "skills"


def adapt_invocation_metadata(skill_path: Path) -> None:
    """Translate Claude's invocation flag to Codex's optional skill metadata."""
    skill_md = skill_path / "SKILL.md"
    contents = skill_md.read_text(encoding="utf-8")
    if not contents.startswith("---\n"):
        raise ValueError(f"{skill_md} does not have YAML frontmatter")
    frontmatter_end = contents.find("\n---", 4)
    if frontmatter_end == -1:
        raise ValueError(f"{skill_md} does not have closed YAML frontmatter")

    frontmatter = contents[4:frontmatter_end]
    was_user_invoked = "disable-model-invocation: true" in frontmatter
    normalized_frontmatter = "".join(
        line
        for line in frontmatter.splitlines(keepends=True)
        if line.rstrip("\r\n") != "disable-model-invocation: true"
    )
    skill_md.write_text(
        "---\n" + normalized_frontmatter + contents[frontmatter_end:], encoding="utf-8"
    )

    if not was_user_invoked:
        return

    metadata = {}
    for line in frontmatter.splitlines():
        key, separator, value = line.partition(": ")
        if separator:
            metadata[key] = value.strip().strip('"')
    name = metadata["name"]
    description = metadata["description"]
    agent_manifest = skill_path / "agents" / "openai.yaml"
    agent_manifest.parent.mkdir()
    agent_manifest.write_text(
        "interface:\n"
        f"  display_name: {json.dumps(name)}\n"
        f"  short_description: {json.dumps(description)}\n"
        "policy:\n"
        "  allow_implicit_invocation: false\n",
        encoding="utf-8",
    )


def main() -> None:
    manifest = json.loads(CLAUDE_MANIFEST.read_text(encoding="utf-8"))
    skills = manifest["skills"]
    if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
        raise ValueError(".claude-plugin/plugin.json must contain a string skills array")

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    seen_names: set[str] = set()
    for relative_path in skills:
        source = ROOT / relative_path.removeprefix("./")
        if not (source / "SKILL.md").is_file():
            raise FileNotFoundError(f"Claude manifest skill is missing: {source}")
        if source.name in seen_names:
            raise ValueError(f"Duplicate skill basename in Claude manifest: {source.name}")
        seen_names.add(source.name)

        destination = OUTPUT / source.name
        shutil.copytree(source, destination)
        adapt_invocation_metadata(destination)


if __name__ == "__main__":
    main()
