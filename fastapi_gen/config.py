from dataclasses import dataclass, field


@dataclass
class ProjectConfig:
    name: str
    db: bool = False
    auth: bool = False
    docker: bool = False
    alembic: bool = False
    tests: bool = False

    @property
    def slug(self) -> str:
        """Snake_case version of the project name for Python modules."""
        return self.name.replace("-", "_").lower()