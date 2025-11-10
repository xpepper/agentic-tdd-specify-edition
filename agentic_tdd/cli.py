"""CLI entry point for agentic-tdd tool."""

import logging
import sys
from pathlib import Path
from typing import Annotated, Literal, Optional, cast

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from .agents import ImplementerAgent, RefactorerAgent, SupervisorAgent, TesterAgent
from .config import load_config_from_cli
from .llm.provider import create_llm
from .models.kata import KataDescription
from .runners import get_runner

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def main(
    kata_file: Annotated[
        Path,
        typer.Argument(
            help="Path to kata description markdown file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    work_dir: Annotated[
        Path,
        typer.Option(
            "--work-dir",
            "-w",
            help="Working directory for implementation",
        ),
    ] = Path("./kata-work"),
    language: Annotated[
        str,
        typer.Option(
            "--language",
            "-l",
            help="Target programming language",
        ),
    ] = "rust",
    provider: Annotated[
        str,
        typer.Option(
            "--provider",
            "-p",
            help="LLM provider (choices: openai, perplexity, deepseek, iflow, custom)",
        ),
    ] = "openai",
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="LLM model name (e.g., gpt-4, llama-3.1-sonar-large-128k-online)",
        ),
    ] = "gpt-4",
    api_key: Annotated[
        Optional[str],  # noqa: UP045 - Typer doesn't support X | None syntax
        typer.Option(
            "--api-key",
            help="API key for LLM provider (or use environment variable)",
        ),
    ] = None,
    base_url: Annotated[
        Optional[str],  # noqa: UP045 - Typer doesn't support X | None syntax
        typer.Option(
            "--base-url",
            help="Custom base URL for LLM provider (for custom provider)",
        ),
    ] = None,
    temperature: Annotated[
        float,
        typer.Option(
            "--temperature",
            "-t",
            help="LLM temperature (0.0-1.0)",
            min=0.0,
            max=1.0,
        ),
    ] = 0.7,
    max_cycles: Annotated[
        int,
        typer.Option(
            "--max-cycles",
            help="Maximum number of TDD cycles",
            min=1,
        ),
    ] = 15,
    max_retries: Annotated[
        int,
        typer.Option(
            "--max-retries",
            help="Maximum retry attempts per agent",
            min=1,
        ),
    ] = 3,
    command_timeout: Annotated[
        int,
        typer.Option(
            "--command-timeout",
            help="Timeout for shell commands in seconds",
            min=1,
        ),
    ] = 300,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Enable verbose logging",
        ),
    ] = False,
) -> None:
    """Autonomous multi-agent TDD CLI tool for kata solving.

    This tool runs the complete TDD cycle for a given kata description,
    using AI agents to write tests, implement solutions, and refactor code.

    Example:
        agentic-tdd katas/fizzbuzz.md --provider openai --model gpt-4
    """
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )

    try:
        # Validate provider choice
        valid_providers = ["openai", "perplexity", "deepseek", "iflow", "custom"]
        if provider not in valid_providers:
            console.print(
                f"[bold red]Error:[/bold red] Invalid provider '{provider}'. "
                f"Choose from: {', '.join(valid_providers)}"
            )
            raise typer.Exit(1)

        # Load configuration
        provider_literal = cast(
            Literal["openai", "perplexity", "deepseek", "iflow", "custom"], provider
        )
        config = load_config_from_cli(
            kata_path=kata_file,
            work_dir=work_dir,
            language=language,
            provider=provider_literal,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_cycles=max_cycles,
            max_retries=max_retries,
            verbose=verbose,
            command_timeout=command_timeout,
        )

        # Load kata description
        console.print("\n[bold blue]📄 Loading kata description...[/bold blue]")
        kata = KataDescription.from_markdown(kata_file)

        # Display session info
        console.print("\n[bold green]🚀 Starting TDD Session[/bold green]")
        console.print(f"[bold]Kata:[/bold] {kata.title}")
        console.print(f"[bold]Work Directory:[/bold] {work_dir}")
        console.print(f"[bold]Language:[/bold] {language}")
        console.print(f"[bold]LLM:[/bold] {provider}/{model}")
        console.print(f"[bold]Max Cycles:[/bold] {max_cycles}")
        console.print()

        # Create language runner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing agents...", total=None)

            # Get language runner
            runner = get_runner(language)

            # Create LLM instance
            llm = create_llm(config.llm_config)

            # Create agents
            tester = TesterAgent(llm=llm, work_dir=work_dir, runner=runner)
            implementer = ImplementerAgent(llm=llm, work_dir=work_dir, runner=runner)
            refactorer = RefactorerAgent(llm=llm, work_dir=work_dir, runner=runner)

            # Create supervisor
            supervisor = SupervisorAgent(
                tester=tester,
                implementer=implementer,
                refactorer=refactorer,
                runner=runner,
                config=config,
                kata=kata,
            )

            progress.update(task, description="[green]✓[/green] Agents initialized")

        # Run TDD session
        console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
        console.print("[bold cyan]Starting TDD Cycle Loop[/bold cyan]")
        console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n")

        session_state = supervisor.run_session()

        # Display results
        console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
        console.print("[bold green]✅ TDD Session Complete[/bold green]")
        console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
        console.print(f"[bold]Total Cycles:[/bold] {len(session_state.cycles)}")
        console.print(f"[bold]Total Commits:[/bold] {session_state.total_commits}")
        console.print(f"[bold]Work Directory:[/bold] {config.work_dir}")
        console.print(
            f"[bold]Started:[/bold] {session_state.started_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        if session_state.completed_at:
            completed_time = session_state.completed_at.strftime("%Y-%m-%d %H:%M:%S")
            console.print(f"[bold]Completed:[/bold] {completed_time}")
            duration = session_state.completed_at - session_state.started_at
            console.print(f"[bold]Duration:[/bold] {duration.total_seconds():.1f}s")
        console.print()

        console.print("[dim]Next steps:[/dim]")
        console.print(f"[dim]  cd {config.work_dir}[/dim]")
        console.print("[dim]  git log --oneline  # View agent commits[/dim]")
        if language == "rust":
            console.print("[dim]  cargo test        # Run tests[/dim]")
            console.print("[dim]  cargo run         # Run code[/dim]")
        console.print()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠️  Session interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    app()
