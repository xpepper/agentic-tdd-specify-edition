"""Shell command execution utilities."""

import subprocess
import time
from pathlib import Path

from ..models.runner import CommandResult


def run_command(
    command: list[str],
    cwd: Path | None = None,
    timeout: int = 30,
    capture_output: bool = True,
) -> CommandResult:
    """Execute a shell command and return the result.

    Args:
        command: Command and arguments as a list
        cwd: Working directory for command execution
        timeout: Timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        CommandResult with execution details

    Raises:
        TimeoutError: If command exceeds timeout
    """
    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )

        output = ""
        if capture_output:
            output = result.stdout + result.stderr

        duration = time.time() - start_time

        return CommandResult(
            command=command,
            exit_code=result.returncode,
            output=output,
            success=(result.returncode == 0),
            duration_seconds=duration,
            timed_out=False,
        )

    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        output = ""
        if capture_output and e.stdout:
            output += e.stdout.decode() if isinstance(e.stdout, bytes) else str(e.stdout)
        if capture_output and e.stderr:
            output += e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)

        return CommandResult(
            command=command,
            exit_code=-1,
            output=output + f"\n\nCommand timed out after {timeout} seconds",
            success=False,
            duration_seconds=duration,
            timed_out=True,
        )

    except Exception as e:
        duration = time.time() - start_time
        return CommandResult(
            command=command,
            exit_code=-1,
            output=f"Error executing command: {str(e)}",
            success=False,
            duration_seconds=duration,
            timed_out=False,
        )
