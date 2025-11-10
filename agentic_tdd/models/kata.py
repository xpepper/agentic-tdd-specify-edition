"""Kata representation models."""

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class KataConstraint(BaseModel):
    """A specific constraint for the kata implementation."""

    description: str = Field(description="Human-readable constraint description")

    applies_to: Literal["code", "tests", "both"] = Field(
        default="code", description="Scope where constraint applies"
    )


class KataDescription(BaseModel):
    """Parsed kata specification."""

    title: str = Field(description="Kata title")

    description: str = Field(description="Full kata description text")

    requirements: list[str] = Field(
        default_factory=list, description="List of behavioral requirements"
    )

    constraints: list[KataConstraint] = Field(
        default_factory=list,
        description=(
            "Implementation constraints (e.g., 'No primitives', 'Single indentation level')"
        ),
    )

    examples: list[str] = Field(default_factory=list, description="Example inputs/outputs")

    source_path: Path = Field(description="Path to original kata markdown file")

    @classmethod
    def from_markdown(cls, path: Path) -> "KataDescription":
        """Parse kata description from markdown file.

        Expected structure:
        # Title
        ## Description
        ...
        ## Requirements
        - Req 1
        - Req 2
        ## Constraints (optional)
        - Constraint 1
        ## Examples (optional)
        ...
        """
        if not path.exists():
            raise FileNotFoundError(f"Kata file not found: {path}")

        content = path.read_text()

        # Parse title (first H1 heading)
        title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Untitled Kata"

        # Parse description section
        description_match = re.search(
            r"## Description\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.MULTILINE
        )
        description = description_match.group(1).strip() if description_match else ""

        # Parse requirements section
        requirements: list[str] = []
        requirements_match = re.search(
            r"## Requirements\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.MULTILINE
        )
        if requirements_match:
            req_text = requirements_match.group(1)
            requirements = [
                line.strip("- ").strip()
                for line in req_text.split("\n")
                if line.strip().startswith("-")
            ]

        # Parse constraints section (optional)
        constraints: list[KataConstraint] = []
        constraints_match = re.search(
            r"## Constraints\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.MULTILINE
        )
        if constraints_match:
            const_text = constraints_match.group(1)
            constraint_lines = [
                line.strip("- ").strip()
                for line in const_text.split("\n")
                if line.strip().startswith("-")
            ]
            constraints = [KataConstraint(description=c) for c in constraint_lines]

        # Parse examples section (optional)
        examples: list[str] = []
        examples_match = re.search(
            r"## Examples\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.MULTILINE
        )
        if examples_match:
            examples_text = examples_match.group(1).strip()
            # Split examples by blank lines or numbered items
            examples = [ex.strip() for ex in re.split(r"\n\n+", examples_text) if ex.strip()]

        return cls(
            title=title,
            description=description,
            requirements=requirements,
            constraints=constraints,
            examples=examples,
            source_path=path,
        )
