"""Git operations utilities."""

from datetime import UTC, datetime
from pathlib import Path

from git import Repo

from ..models.agent import GitCommitInfo


class GitOperations:
    """Wrapper for git operations using GitPython."""

    def __init__(self, repo_path: Path):
        """Initialize git operations for a repository.

        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = repo_path
        self.repo: Repo | None = None

    def init(self) -> None:
        """Initialize a new git repository."""
        repo = Repo.init(self.repo_path)
        self.repo = repo

        # Configure git user if not set
        with repo.config_writer() as config:
            try:
                config.get_value("user", "name")
            except Exception:
                config.set_value("user", "name", "Agentic TDD")
            try:
                config.get_value("user", "email")
            except Exception:
                config.set_value("user", "email", "agentic-tdd@localhost")

    def ensure_repo(self) -> Repo:
        """Ensure repo is loaded, raise if not initialized."""
        if self.repo is None:
            if (self.repo_path / ".git").exists():
                self.repo = Repo(self.repo_path)
            else:
                raise RuntimeError(f"Git repository not initialized at {self.repo_path}")
        return self.repo

    def add(self, file_paths: list[Path]) -> None:
        """Stage files for commit.

        Args:
            file_paths: List of file paths to stage
        """
        repo = self.ensure_repo()
        # Convert to relative paths from repo root
        relative_paths = [str(p.relative_to(self.repo_path)) for p in file_paths]
        repo.index.add(relative_paths)

    def commit(self, message: str) -> str:
        """Create a commit with staged changes.

        Args:
            message: Commit message

        Returns:
            Commit SHA
        """
        repo = self.ensure_repo()
        commit = repo.index.commit(message)
        return commit.hexsha

    def get_recent_commits(self, limit: int = 5) -> list[GitCommitInfo]:
        """Get recent commits.

        Args:
            limit: Maximum number of commits to retrieve

        Returns:
            List of commit info objects
        """
        repo = self.ensure_repo()

        commits: list[GitCommitInfo] = []
        for commit in repo.iter_commits(max_count=limit):
            # Convert PathLike to str for files_changed
            files_changed = [str(f) for f in commit.stats.files.keys()]
            # Ensure message is str (can be bytes)
            message = (
                commit.message
                if isinstance(commit.message, str)
                else commit.message.decode("utf-8")
            )
            commits.append(
                GitCommitInfo(
                    sha=commit.hexsha[:8],  # Short SHA
                    message=message.strip(),
                    author=str(commit.author),
                    timestamp=datetime.fromtimestamp(commit.committed_date, tz=UTC),
                    files_changed=files_changed,
                )
            )

        return commits

    def revert_to_commit(self, commit_sha: str) -> None:
        """Hard reset to a specific commit.

        Args:
            commit_sha: Commit SHA to revert to
        """
        repo = self.ensure_repo()
        repo.git.reset("--hard", commit_sha)

    def get_status(self) -> dict[str, list[str]]:
        """Get repository status.

        Returns:
            Dictionary with 'modified', 'staged', 'untracked' file lists
        """
        repo = self.ensure_repo()

        return {
            "modified": [item.a_path for item in repo.index.diff(None) if item.a_path is not None],
            "staged": [item.a_path for item in repo.index.diff("HEAD") if item.a_path is not None],
            "untracked": repo.untracked_files,
        }

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes.

        Returns:
            True if there are uncommitted changes
        """
        repo = self.ensure_repo()
        return repo.is_dirty() or len(repo.untracked_files) > 0

    def get_last_commit_sha(self) -> str | None:
        """Get the last commit SHA.

        Returns:
            Last commit SHA or None if no commits exist
        """
        repo = self.ensure_repo()
        try:
            return repo.head.commit.hexsha
        except ValueError:
            # No commits yet
            return None
