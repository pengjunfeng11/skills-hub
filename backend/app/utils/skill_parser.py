import re
import frontmatter


def parse_skill_md(content: str) -> dict:
    """Parse a SKILL.md file, extracting frontmatter metadata and body."""
    post = frontmatter.loads(content)
    return {
        "metadata": dict(post.metadata),
        "body": post.content,
        "name": post.metadata.get("name"),
        "display_name": post.metadata.get("display_name") or post.metadata.get("title"),
        "description": post.metadata.get("description"),
        "tags": post.metadata.get("tags", []),
        "category": post.metadata.get("category"),
    }


def validate_skill_name(name: str) -> bool:
    """Validate that skill name is kebab-case."""
    return bool(re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", name))


def validate_semver(version: str) -> bool:
    """Basic semver validation."""
    return bool(re.match(r"^\d+\.\d+\.\d+(?:-[\w.]+)?(?:\+[\w.]+)?$", version))
