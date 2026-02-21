"""Skills Hub MCP Server for Claude Code integration.

Provides tools for discovering and retrieving Skills from a Skills Hub instance.

Usage:
    skills-hub-mcp --server https://skills.company.internal

Environment variables:
    SKILLS_HUB_URL: Base URL of the Skills Hub instance
    SKILLS_HUB_API_KEY: API key for authentication
"""

import argparse
import os
import sys

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("skills-hub")

_client: httpx.AsyncClient | None = None
_base_url: str = ""
_api_key: str = ""


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=_base_url,
            headers={"Authorization": f"Bearer {_api_key}"},
            timeout=30.0,
        )
    return _client


@mcp.tool()
async def list_skills() -> str:
    """List all available skills from the Skills Hub catalog.

    Returns a formatted list of skills with their names, descriptions, versions, and tags.
    """
    client = _get_client()
    resp = await client.get("/api/v1/skills/catalog")
    resp.raise_for_status()
    data = resp.json()

    if not data["skills"]:
        return "No skills available in the catalog."

    lines = []
    for skill in data["skills"]:
        tags = ", ".join(skill.get("tags", []))
        tag_str = f" [{tags}]" if tags else ""
        lines.append(f"- **{skill['name']}** v{skill['version']}{tag_str}")
        if skill.get("description"):
            lines.append(f"  {skill['description']}")
    return "\n".join(lines)


@mcp.tool()
async def get_skill(name: str, version: str | None = None) -> str:
    """Get the full content of a specific skill (SKILL.md).

    Args:
        name: The skill name (kebab-case, e.g. "deploy-k8s")
        version: Optional specific version (semver). Defaults to latest.

    Returns the SKILL.md content that should be followed as instructions.
    """
    client = _get_client()
    params = {}
    if version:
        params["version"] = version
    resp = await client.get(f"/api/v1/skills/{name}/raw", params=params)
    resp.raise_for_status()
    data = resp.json()
    return f"# Skill: {data['name']} (v{data['version']})\n\n{data['content']}"


@mcp.tool()
async def resolve_skills(skills: list[str]) -> str:
    """Batch resolve multiple skills by name, returning their full content.

    Args:
        skills: List of skill specs, e.g. ["deploy-k8s", "code-review@1.2.0"]

    Returns the full content of all resolved skills.
    """
    client = _get_client()
    resp = await client.post("/api/v1/skills/resolve", json={"skills": skills})
    resp.raise_for_status()
    data = resp.json()

    if not data["skills"]:
        return "No skills could be resolved from the provided list."

    parts = []
    for skill in data["skills"]:
        header = f"# Skill: {skill['name']} (v{skill['version']})"
        parts.append(f"{header}\n\n{skill['content']}")
        if skill.get("files"):
            parts.append("\n## Additional Files\n")
            for path, content in skill["files"].items():
                parts.append(f"### {path}\n```\n{content}\n```\n")
    return "\n---\n\n".join(parts)


@mcp.tool()
async def search_skills(query: str) -> str:
    """Search for skills by keyword in the catalog.

    Args:
        query: Search keyword to match against skill names and descriptions.

    Returns matching skills from the catalog.
    """
    client = _get_client()
    resp = await client.get("/api/v1/skills/catalog")
    resp.raise_for_status()
    data = resp.json()

    query_lower = query.lower()
    matches = []
    for skill in data["skills"]:
        name_match = query_lower in skill["name"].lower()
        desc_match = skill.get("description") and query_lower in skill["description"].lower()
        tag_match = any(query_lower in t.lower() for t in skill.get("tags", []))
        if name_match or desc_match or tag_match:
            matches.append(skill)

    if not matches:
        return f"No skills found matching '{query}'."

    lines = []
    for skill in matches:
        tags = ", ".join(skill.get("tags", []))
        tag_str = f" [{tags}]" if tags else ""
        lines.append(f"- **{skill['name']}** v{skill['version']}{tag_str}")
        if skill.get("description"):
            lines.append(f"  {skill['description']}")
    return "\n".join(lines)


def main():
    global _base_url, _api_key

    parser = argparse.ArgumentParser(description="Skills Hub MCP Server")
    parser.add_argument("--server", help="Skills Hub server URL")
    args = parser.parse_args()

    _base_url = args.server or os.environ.get("SKILLS_HUB_URL", "")
    _api_key = os.environ.get("SKILLS_HUB_API_KEY", "")

    if not _base_url:
        print("Error: --server URL or SKILLS_HUB_URL env var required", file=sys.stderr)
        sys.exit(1)

    if not _api_key:
        print("Error: SKILLS_HUB_API_KEY env var required", file=sys.stderr)
        sys.exit(1)

    mcp.run()


if __name__ == "__main__":
    main()
