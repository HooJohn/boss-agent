from pathlib import Path
from typing import Optional


class WorkspaceManager:
    root: Path
    session_workspace: Path

    def __init__(
        self,
        root: Path,
        session_workspace: Optional[Path] = None,
        container_workspace: Optional[Path] = None,
    ):
        self.root = root.absolute()
        self.session_workspace = (
            session_workspace.absolute() if session_workspace else self.root
        )
        self.container_workspace = container_workspace

    def workspace_path(self, path: Path | str, for_write: bool = False) -> Path:
        """Given a path, possibly in a container workspace, return the absolute local path."""
        path = Path(path)

        if for_write:
            # All writes go to the session workspace
            if not path.is_absolute():
                return self.session_workspace / path
            if self.container_workspace and path.is_relative_to(
                self.container_workspace
            ):
                return self.session_workspace / path.relative_to(
                    self.container_workspace
                )
            return path

        # For reads, check session workspace first, then root
        if not path.is_absolute():
            session_path = self.session_workspace / path
            if session_path.exists():
                return session_path
            return self.root / path

        if self.container_workspace and path.is_relative_to(self.container_workspace):
            relative_path = path.relative_to(self.container_workspace)
            session_path = self.session_workspace / relative_path
            if session_path.exists():
                return session_path
            return self.root / relative_path

        return path

    def container_path(self, path: Path | str) -> Path:
        """Given a path, possibly in the local workspace, return the absolute container path.
        If there is no container workspace, return the absolute local path.
        """
        path = Path(path)
        if not path.is_absolute():
            if self.container_workspace:
                return self.container_workspace / path
            else:
                return self.root / path
        if self.container_workspace and path.is_relative_to(self.root):
            return self.container_workspace / path.relative_to(self.root)
        return path

    def relative_path(self, path: Path | str) -> Path:
        """Given a path, return the relative path from the workspace root.
        If the path is not under the workspace root, returns the absolute path.
        """
        path = Path(path)
        abs_path = self.workspace_path(path)
        try:
            return abs_path.relative_to(self.root.absolute())
        except ValueError:
            return abs_path
