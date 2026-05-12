"""Application entry point, environment setup, & main loop."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.infrastructure.config import settings
from src.infrastructure.models import resolve_model, ModelResolutionError
from src.utils.logging import setup_logging
from src.infrastructure.docker.manager import cleanup_stale_sandboxes
from .app import run_agent_turn
from .ui import console, StreamManager
from .tui import print_banner, select_provider, select_model
from .settings_menu import open_settings_menu
from langchain_core.messages import HumanMessage


def ensure_dirs() -> None:
    for d in [settings.WORKSPACE_BASE, settings.OUTPUT_DIR, settings.LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)


async def main() -> None:
    load_dotenv()
    setup_logging(str(settings.LOG_DIR), settings.LOG_LEVEL)
    ensure_dirs()
    cleanup_stale_sandboxes()

    llm = None
    while not llm:
        print_banner()
        provider = await select_provider()
        if provider == "exit":
            console.print("\n[yellow]👋 Exiting Sandman. Goodbye![/yellow]")
            return
        model_name = await select_model(provider)
        if not model_name:
            continue
        try:
            llm = resolve_model(provider, model_name)
            console.print(
                f"[green]✅ Model loaded: [bold]{model_name}[/bold] ({provider})[/green]\n"
            )
        except Exception as e:
            console.print(f"[red]❌ {e}[/red]\n")

    import os

    env = {
        "PYTHONPATH": os.getcwd(),
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),  # Windows compatibility
        "HOME": os.environ.get("HOME", ""),
    }

    try:
        import src.infrastructure.mcp.server
    except Exception as e:
        console.print(f"[red][MCP IMPORT ERROR] The MCP server failed to load:\n{e}[/red]")
        sys.exit(1)

    mcp_client = MultiServerMCPClient(
        {
            "sandbox": {
                "command": sys.executable,
                "args": ["-m", "src.infrastructure.mcp.server"],
                "transport": "stdio",
                "env": env,
            }
        }
    )

    stream = StreamManager()

    try:
        tools = await mcp_client.get_tools()
        chat_history = []
        console.print("[dim]Commands: /settings • /clear • exit/quit • Ctrl+C to interrupt[/dim]")

        while True:
            try:
                user_input = console.input("\n[bold cyan]Sandman > [/bold cyan]").strip()
            except EOFError:
                break

            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                break
            if user_input.lower() == "/settings":
                await open_settings_menu()
                continue
            if user_input.lower() == "/clear":
                stream.clear()
                continue

            chat_history.append(HumanMessage(content=user_input))
            if len(chat_history) > settings.MAX_CHAT_HISTORY:
                chat_history = chat_history[-settings.MAX_CHAT_HISTORY:]

            await stream.log_system(f"Processing: {user_input[:60]}...")
            try:
                chat_history = await run_agent_turn(chat_history, llm, tools, stream)
            except Exception as e:
                await stream.log_system(f"[bold red]Execution Error:[/bold red] {e}")
                if "unauthorized" in str(e).lower() or "401" in str(e):
                    await stream.log_system("[yellow]Tip: Your API key or Base URL might be incorrect. Check your /settings.[/yellow]")
    except KeyboardInterrupt:
        pass
    finally:
        console.print("\n[yellow][SYSTEM] Shutting down...[/yellow]")


def cli_entry() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
