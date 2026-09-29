"""Main entry point for the Scientific Articles Engine CLI."""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import load_config
from .core.state import create_initial_state
from .graph.workflow import create_async_workflow
from .utils.logger import setup_logging

console = Console()


@click.group()
@click.option("--config", "-c", default="config.yaml", help="Path to configuration file")
@click.option("--log-level", default="INFO", help="Logging level")
@click.pass_context
def cli(ctx: click.Context, config: str, log_level: str) -> None:
    """Scientific Articles Engine - Multi-agent system for generating scientific articles.

    This CLI tool orchestrates multiple AI agents to:
    1. Search for relevant academic papers
    2. Write comprehensive articles
    3. Review and refine content
    4. Generate visualizations

    Includes Human-in-the-Loop (HITL) approval points for quality control.
    """
    # Setup logging
    setup_logging(level=log_level)

    # Store config path in context
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


@cli.command()
@click.argument("topic")
@click.option("--output", "-o", help="Output file path (default: article.md)")
@click.option("--thread-id", default="default", help="Thread ID for checkpointing")
@click.option("--auto-approve", is_flag=True, help="Auto-approve HITL points (for testing)")
@click.pass_context
def generate(
    ctx: click.Context,
    topic: str,
    output: str | None,
    thread_id: str,
    auto_approve: bool,
) -> None:
    """Generate a scientific article on the specified TOPIC.

    Example:
        scientific-articles-engine generate "Transformer Architectures in NLP"
    """
    coro = _generate_article(ctx, topic, output, thread_id, auto_approve)
    if sys.platform == "win32":
        asyncio.run(coro, loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(coro)


async def _generate_article(
    ctx: click.Context,
    topic: str,
    output: str | None,
    thread_id: str,
    auto_approve: bool,
) -> None:
    """Async implementation of article generation."""
    try:
        # Load configuration
        config_path = ctx.obj["config_path"]
        config = load_config(config_path)

        console.print(Panel.fit(
            f"[bold cyan]Scientific Articles Engine[/bold cyan]\n"
            f"Topic: [yellow]{topic}[/yellow]",
            title="Starting Generation",
        ))

        # Create workflow
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating workflow...", total=None)
            workflow = await create_async_workflow(config)
            progress.update(task, completed=True)

        # Create initial state
        initial_state = create_initial_state(topic)
        workflow_config = {"configurable": {"thread_id": thread_id}}

        # Phase 1: Search and outline
        console.print("\n[bold]Phase 1: Searching papers and generating outline[/bold]")
        state = None
        # Execute the search and outline phase asynchronously.
        # The workflow yields intermediate states as it progresses through
        # the search and outline phase. astream asynchronously iterates over
        # those states; the first parameter is the initial state, and the
        # second parameter is the workflow configuration.
        async for s in workflow.astream(
            initial_state, workflow_config, stream_mode="values"
        ):
            state = s

        if state is None or state.get("error_message"):
            error_message = (state or {}).get("error_message", "Workflow produced no state")
            raise RuntimeError(f"Search phase failed: {error_message}")

        # HITL Point 1: Review sources
        console.print("\n[bold yellow]HITL Checkpoint 1: Review Sources[/bold yellow]")
        console.print(f"Found {len(state['papers'])} papers")
        console.print("\n[cyan]Outline:[/cyan]")
        console.print(Panel(state["outline"], title="Article Outline", expand=False))

        if not auto_approve:
            approve = click.confirm("\nApprove sources and outline?", default=True)
        else:
            console.print("[dim]Auto-approving (--auto-approve flag set)[/dim]")
            approve = True

        if not approve:
            console.print("[red]Generation cancelled by user.[/red]")
            return

        # Update the checkpointed state, then resume from the HITL pause.
        workflow_config = await workflow.aupdate_state(
            workflow_config, {"searcher_approved": True}
        )

        # Phase 2: Writing and reviewing
        console.print("\n[bold]Phase 2: Writing and reviewing article[/bold]")
        console.print("[dim]This may take several minutes...[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Writing and reviewing...", total=None)

            async for s in workflow.astream(
                None, workflow_config, stream_mode="values"
            ):
                state = s
                if "article" in s and s.get("review"):
                    progress.update(
                        task,
                        description=f"Revision {state['revision_count']}: "
                        f"Score {state['review'].overall_score:.1f}/10",
                    )

            progress.update(task, completed=True)

        if state is None:
            raise RuntimeError("Writing/review phase produced no workflow state")
        if state.get("error_message"):
            raise RuntimeError(
                f"Writing/review phase failed: {state['error_message']}"
            )

        # HITL Point 2: Review final article
        article = state["article"]
        if article is None:
            raise RuntimeError("Writing/review phase ended without producing an article")

        console.print("\n[bold yellow]HITL Checkpoint 2: Review Final Article[/bold yellow]")
        console.print(f"[green]Article: {article.title}[/green]")
        console.print(f"Word count: {article.word_count}")
        console.print(f"Version: {article.version}")
        console.print(f"\n[cyan]Abstract:[/cyan]\n{article.abstract}")

        if not auto_approve:
            approve = click.confirm("\nApprove final article?", default=True)
        else:
            console.print("[dim]Auto-approving (--auto-approve flag set)[/dim]")
            approve = True

        if not approve:
            console.print("[red]Article rejected. Workflow terminated.[/red]")
            return

        # Read the latest checkpoint without the older checkpoint_id from the prior resume.
        thread_config = {"configurable": {"thread_id": thread_id}}
        workflow_config = (await workflow.aget_state(thread_config)).config

        # Update the checkpointed state, then resume from the final HITL pause.
        workflow_config = await workflow.aupdate_state(
            workflow_config, {"final_approved": True}
        )

        console.print("\n[bold]Phase 3: Generating visualizations[/bold]")
        async for s in workflow.astream(
            None, workflow_config, stream_mode="values"
        ):
            state = s

        # Save article
        output_path = output or f"{topic.replace(' ', '_')}.md"
        _save_article(state["article"], state["visualizations"], Path(output_path))

        console.print("\n[bold green]✓ Article generated successfully![/bold green]")
        console.print(f"Output: {output_path}")
        console.print(f"Visualizations: {len(state['visualizations'])}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise


def _save_article(article, visualizations, output_path: Path) -> None:
    """Save article to file with visualizations.

    Args:
        article: Article object
        visualizations: List of visualizations
        output_path: Output file path
    """
    content_parts = [article.to_markdown()]

    if visualizations:
        content_parts.append("\n\n---\n\n# Visualizations\n\n")
        for viz in visualizations:
            content_parts.append(viz.to_markdown())
            content_parts.append("\n\n")

    output_path.write_text("\n".join(content_parts))


@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
def validate_config(config_file: str) -> None:
    """Validate a configuration file.

    Example:
        scientific-articles-engine validate-config config.yaml
    """
    try:
        config = load_config(config_file)
        console.print("[green]✓ Configuration is valid[/green]")
        console.print(f"\nProvider: {config.llm.provider}")
        console.print(f"Model: {config.llm.model}")
        console.print(f"Database: {'Enabled' if config.database.enabled else 'Disabled'}")
    except Exception as e:
        console.print(f"[red]✗ Configuration error:[/red] {e}")
        raise


@cli.command()
def version() -> None:
    """Show version information."""
    from . import __version__

    console.print(f"Scientific Articles Engine v{__version__}")


if __name__ == "__main__":
    cli()
