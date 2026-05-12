"""Interactive Terminal UI with navigation & dynamic model browsing."""

import os
import questionary
from rich.console import Console
from rich.panel import Panel
from .model_browser import get_available_models

console = Console()


def print_banner() -> None:
    console.print(
        Panel(
            "[bold cyan]Sandman[/bold cyan] — Autonomous Sandbox Code Runner\n"
            "[dim]Secure • Self-Healing • Multi-Language • Live Execution[/dim]",
            title="🤖 AI Agent",
            border_style="cyan",
            padding=(1, 2),
        )
    )


async def select_provider() -> str:
    providers = [
        {"name": "🐋 Ollama (Local)", "value": "ollama"},
        {"name": "🔑 OpenAI / Compatible API (BYOK)", "value": "byok"},
        {"name": "✨ Google Gemini", "value": "google"},
        {"name": "☁️  Ollama Cloud", "value": "ollama_cloud"},
        {"name": "← Back / Exit", "value": "exit"},
    ]
    choice = await questionary.select(
        "Select LLM Provider:",
        choices=[p["name"] for p in providers],
        use_shortcuts=True,
        instruction="(↑↓ navigate, Enter select, Esc back)",
        style=questionary.Style([("selected", "bold cyan"), ("pointer", "cyan")]),
    ).ask_async(patch_stdout=True)

    if not choice or choice == "← Back / Exit":
        return "exit"
    return next(p["value"] for p in providers if p["name"] == choice)


async def select_model(provider: str) -> str:
    console.print(f"\n[bold yellow]🔍 Fetching available models for {provider}...[/bold yellow]")
    models = get_available_models(provider)

    if not models:
        console.print("[dim]⚠️  No models found via API. You can enter a custom model name.[/dim]")
        custom = await questionary.text(
            "Enter model name:", instruction="(Leave empty to go back)"
        ).ask_async(patch_stdout=True)
        return custom.strip() if custom else ""

    choices = models + ["✍️  Enter custom model name", "← Back"]
    selected = await questionary.autocomplete(
        "Select or search model (Type to filter, ↑↓ navigate, Enter select, Esc back):",
        choices=choices,
        style=questionary.Style([("selected", "bold cyan"), ("pointer", "cyan")]),
    ).ask_async(patch_stdout=True)

    if not selected or selected == "← Back":
        return ""
    if selected == "✍️  Enter custom model name":
        custom = await questionary.text(
            "Enter model name:", instruction="(Leave empty to go back)"
        ).ask_async(patch_stdout=True)
        return custom.strip() if custom else ""
    return selected
