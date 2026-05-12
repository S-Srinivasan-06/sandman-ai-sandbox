"""Interactive runtime settings menu."""

import questionary
from rich.console import Console
from src.infrastructure.config import settings

console = Console()


async def open_settings_menu() -> None:
    console.print("\n[bold yellow]⚙️  Sandman Runtime Settings[/bold yellow]")
    console.print(
        "[dim]Changes apply immediately to new sandboxes/sessions. Not persisted to .env.[/dim]\n"
    )

    while True:
        choice = await questionary.select(
            "Select setting to modify:",
            choices=[
                f"⏱️  Execution Timeout: {settings.EXEC_TIMEOUT}s",
                f"📦 Dep Install Timeout: {settings.DEP_INSTALL_TIMEOUT}s",
                f"🔄 Max Retries: {settings.MAX_RETRIES}",
                f"💬 Chat History Limit: {settings.MAX_CHAT_HISTORY}",
                f"🌐 Allow Network Default: {settings.ALLOW_NETWORK_DEFAULT}",
                f"🐋 Ollama VRAM Cleanup: {settings.ENABLE_OLLAMA_VRAM_CLEANUP}",
                f"📝 Log Level: {settings.LOG_LEVEL}",
                "← Back to Chat",
            ],
            instruction="(↑↓ navigate, Enter select, Esc back)",
        ).ask_async()

        if not choice or "Back to Chat" in choice:
            break

        if "Execution Timeout" in choice:
            val = await questionary.text(
                "Enter new timeout (seconds):", default=str(settings.EXEC_TIMEOUT)
            ).ask_async()
            if val and val.isdigit():
                settings.EXEC_TIMEOUT = int(val)
        elif "Dep Install Timeout" in choice:
            val = await questionary.text(
                "Enter new dep timeout (seconds):", default=str(settings.DEP_INSTALL_TIMEOUT)
            ).ask_async()
            if val and val.isdigit():
                settings.DEP_INSTALL_TIMEOUT = int(val)
        elif "Max Retries" in choice:
            val = await questionary.text(
                "Enter max retries:", default=str(settings.MAX_RETRIES)
            ).ask_async()
            if val and val.isdigit():
                settings.MAX_RETRIES = int(val)
        elif "Chat History Limit" in choice:
            val = await questionary.text(
                "Enter max chat history messages:", default=str(settings.MAX_CHAT_HISTORY)
            ).ask_async()
            if val and val.isdigit():
                settings.MAX_CHAT_HISTORY = int(val)
        elif "Allow Network" in choice:
            settings.ALLOW_NETWORK_DEFAULT = await questionary.confirm(
                "Allow network access by default?", default=settings.ALLOW_NETWORK_DEFAULT
            ).ask_async()
        elif "Ollama VRAM" in choice:
            settings.ENABLE_OLLAMA_VRAM_CLEANUP = await questionary.confirm(
                "Enable Ollama VRAM cleanup on exit?", default=settings.ENABLE_OLLAMA_VRAM_CLEANUP
            ).ask_async()
        elif "Log Level" in choice:
            level = await questionary.select(
                "Select log level:",
                choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                default=settings.LOG_LEVEL,
            ).ask_async()
            if level:
                settings.LOG_LEVEL = level

        console.print(f"[green]✅ Updated successfully.[/green]\n")
