from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from loguru import logger

from asta.core_engine.graph import AstaGraph, AstaState
from asta.core_engine.event_bus import EventBus, Event

console = Console()


class CLIGateway:
    """Command Line Interface for interacting with ASTA via the rich terminal."""

    def __init__(self, graph: AstaGraph, event_bus: EventBus) -> None:
        self.graph = graph
        self.event_bus = event_bus

    async def start_interactive_session(self) -> None:
        """Starts the interactive CLI loop."""
        console.print(Panel.fit("[bold blue]ASTA OS: Autonomous Agent Interface[/bold blue]\nType 'exit' to quit.", border_style="blue"))

        while True:
            try:
                user_input = Prompt.ask("[bold green]You[/bold green]")
                if user_input.strip().lower() in ["exit", "quit"]:
                    console.print("[bold red]Shutting down ASTA...[/bold red]")
                    break

                if not user_input.strip():
                    continue

                await self.process_command(user_input)

            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold red]Shutting down ASTA...[/bold red]")
                break
            except Exception as e:
                logger.error(f"CLI Error: {e}")
                console.print(f"[bold red]System Error: {e}[/bold red]")

    async def process_command(self, command: str) -> None:
        """Packages the command into the State and routes it through the graph."""

        # Publish an event to track input across the system
        await self.event_bus.publish(Event(type="USER_INPUT_RECEIVED", payload={"source": "cli", "command": command}))

        # Initialize the global state with the user's input
        state = AstaState()
        state.m_active["user_activity"] = command

        console.print("[dim italic]Routing command through AstaGraph...[/dim italic]")

        try:
            # Execute the DAG router
            final_state = await self.graph.execute(state)

            # Extract any agent responses meant for the user
            responses = [msg["content"] for msg in final_state.messages if msg.get("role") == "agent"]

            if responses:
                for response in responses:
                    console.print(Panel(response, title="[bold magenta]Asta[/bold magenta]", border_style="magenta"))
            else:
                console.print("[dim]Task executed. No verbal response required.[/dim]")

        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            console.print(f"[bold red]Graph Execution Failed: {e}[/bold red]")
