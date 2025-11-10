"""Logging utilities with Rich console output."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from ..models.agent import AgentRole
from ..models.cycle import TDDPhase

# Global console instance
console = Console()


def log_phase_start(phase: TDDPhase) -> None:
    """Log the start of a TDD phase.

    Args:
        phase: TDD phase being started
    """
    phase_styles = {
        TDDPhase.TESTING: ("red", "🔴"),
        TDDPhase.IMPLEMENTING: ("green", "🟢"),
        TDDPhase.REFACTORING: ("blue", "🔵"),
        TDDPhase.COMPLETE: ("green", "✓"),
        TDDPhase.FAILED: ("red", "✗"),
    }

    color, emoji = phase_styles[phase]
    console.print(
        Panel(
            f"[bold]{emoji} Starting {phase.value.upper()} Phase[/bold]",
            style=color,
            expand=False,
        )
    )


def log_phase_complete(phase: TDDPhase) -> None:
    """Log the completion of a TDD phase.

    Args:
        phase: TDD phase that completed
    """
    phase_styles = {
        TDDPhase.TESTING: ("red", "✓"),
        TDDPhase.IMPLEMENTING: ("green", "✓"),
        TDDPhase.REFACTORING: ("blue", "✓"),
        TDDPhase.COMPLETE: ("green", "✓"),
        TDDPhase.FAILED: ("red", "✗"),
    }

    color, checkmark = phase_styles[phase]
    console.print(f"[{color}]{checkmark} {phase.value.upper()} phase complete[/{color}]")


def log_agent_action(role: AgentRole, action: str, details: str | None = None) -> None:
    """Log an agent action.

    Args:
        role: Agent role performing the action
        action: Description of the action
        details: Optional additional details
    """
    role_styles = {
        AgentRole.TESTER: ("yellow", "🧪"),
        AgentRole.IMPLEMENTER: ("cyan", "⚙️"),
        AgentRole.REFACTORER: ("magenta", "♻️"),
        AgentRole.SUPERVISOR: ("white", "👁️"),
    }

    color, emoji = role_styles[role]
    message = f"[{color}]{emoji} {role.value}:[/{color}] {action}"
    console.print(message)

    if details:
        console.print(f"  [dim]{details}[/dim]")


def log_command(command: str, work_dir: str) -> None:
    """Log a command being executed.

    Args:
        command: Command string
        work_dir: Working directory
    """
    console.print(f"[dim]$ {command}[/dim]")
    console.print(f"[dim]  (in {work_dir})[/dim]")


def log_command_result(success: bool, stdout: str, stderr: str) -> None:
    """Log command execution result.

    Args:
        success: Whether command succeeded
        stdout: Standard output
        stderr: Standard error
    """
    if success:
        console.print("[green]✓ Command succeeded[/green]")
    else:
        console.print("[red]✗ Command failed[/red]")

    if stdout.strip():
        console.print("[dim]stdout:[/dim]")
        console.print(stdout)

    if stderr.strip():
        console.print("[dim]stderr:[/dim]")
        console.print(stderr)


def log_test_results(passed: int, failed: int, total: int) -> None:
    """Log test execution results.

    Args:
        passed: Number of tests passed
        failed: Number of tests failed
        total: Total number of tests
    """
    table = Table(show_header=True, header_style="bold")
    table.add_column("Status", style="dim")
    table.add_column("Count", justify="right")

    table.add_row("Passed", f"[green]{passed}[/green]")
    table.add_row("Failed", f"[red]{failed}[/red]")
    table.add_row("Total", str(total))

    console.print(table)


def log_error(message: str, details: str | None = None) -> None:
    """Log an error message.

    Args:
        message: Error message
        details: Optional error details
    """
    console.print(f"[bold red]✗ Error:[/bold red] {message}")
    if details:
        console.print(f"[dim]{details}[/dim]")


def log_warning(message: str) -> None:
    """Log a warning message.

    Args:
        message: Warning message
    """
    console.print(f"[yellow]⚠ Warning:[/yellow] {message}")


def log_info(message: str) -> None:
    """Log an info message.

    Args:
        message: Info message
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def log_success(message: str) -> None:
    """Log a success message.

    Args:
        message: Success message
    """
    console.print(f"[bold green]✓ {message}[/bold green]")


def log_markdown(content: str) -> None:
    """Log markdown-formatted content.

    Args:
        content: Markdown content to display
    """
    md = Markdown(content)
    console.print(md)


def log_cycle_summary(cycle_number: int, phase: TDDPhase, success: bool) -> None:
    """Log a summary of a completed cycle.

    Args:
        cycle_number: Cycle number
        phase: Phase reached
        success: Whether cycle was successful
    """
    status_color = "green" if success else "red"
    status_text = "✓ Complete" if success else "✗ Failed"

    console.print(
        Panel(
            f"[bold]Cycle {cycle_number}[/bold]\n"
            f"Phase: {phase.value}\n"
            f"Status: [{status_color}]{status_text}[/{status_color}]",
            title="Cycle Summary",
            expand=False,
        )
    )


def log_session_complete(cycles_completed: int, kata_name: str) -> None:
    """Log session completion.

    Args:
        cycles_completed: Number of cycles completed
        kata_name: Name of the kata
    """
    console.print(
        Panel(
            f"[bold green]🎉 Session Complete![/bold green]\n\n"
            f"Kata: {kata_name}\n"
            f"Cycles: {cycles_completed}",
            title="Success",
            style="green",
            expand=False,
        )
    )
