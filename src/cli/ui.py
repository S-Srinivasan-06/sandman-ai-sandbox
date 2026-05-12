"""Simple terminal UI helpers."""

import asyncio
import json
import ast
from datetime import datetime
from rich.console import Console

console = Console()

class StreamManager:
    """Simple CLI execution logger."""

    def __init__(self):
        self._lock = asyncio.Lock()

    async def log_tool_call(self, name: str, args: dict) -> None:
        async with self._lock:
            console.print(f"\n[bold yellow]Running tool: {name.upper()}[/bold yellow]")
            for k, v in args.items():
                # Format sandbox_id or other long IDs to be recognizable but not overwhelming if needed
                # for now just print them
                console.print(f"  [yellow]{k}: {v}[/yellow]")

    async def log_tool_result(self, content: str) -> None:
        async with self._lock:
            try:
                data = self._parse_content(content)
                
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = item.get("text", "")
                            # Try to parse nested JSON (sandbox results)
                            try:
                                nested = json.loads(text)
                                if isinstance(nested, dict) and ("exit_code" in nested or "stdout" in nested):
                                    self._print_sandbox_result(nested)
                                    continue
                            except:
                                pass
                            
                            # Standard text result
                            if "successfully" in text.lower() and "error" not in text.lower():
                                console.print(f"[green]✅ {text}[/green]")
                            else:
                                console.print(f"[blue]📤 {text}[/blue]")
                        else:
                            console.print(f"[blue]📤 {item}[/blue]")
                elif isinstance(data, dict) and ("exit_code" in data or "stdout" in data):
                    self._print_sandbox_result(data)
                else:
                    console.print(f"[blue]📤 {content}[/blue]")
            except Exception:
                # Fallback to raw output if parsing fails
                console.print(f"[blue]📤 {content}[/blue]")

    def _parse_content(self, content: str):
        if not content:
            return ""
        try:
            return json.loads(content)
        except:
            try:
                # Handle cases where it's a Python-style string repr (common in LangChain)
                return ast.literal_eval(content)
            except:
                return content

    def _print_sandbox_result(self, result: dict) -> None:
        exit_code = result.get("exit_code", 0)
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        
        if exit_code == 0:
            if stdout:
                console.print(f"[dim]{stdout}[/dim]")
            if "successfully" in stdout.lower() or not stdout:
                # Don't double-print if it was just a "success" message
                if not ("successfully" in stdout.lower() and len(stdout) < 100):
                    console.print("[green]✅ Execution finished successfully[/green]")
        else:
            console.print(f"[bold red]❌ Execution failed (Exit code: {exit_code})[/bold red]")
            if stdout:
                console.print(f"[dim]STDOUT:[/dim]\n{stdout}")
            if stderr:
                console.print(f"[red]STDERR:[/red]\n{stderr}")

    async def log_ai(self, content: str) -> None:
        async with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            # If it's short, keep it on one line, otherwise use a header
            if len(content) < 100:
                console.print(f"[{ts}] [bold green]🤖 AI:[/bold green] {content}")
            else:
                console.print(f"[{ts}] [bold green]🤖 AI Response:[/bold green]")
                console.print(content)

    async def log_system(self, msg: str) -> None:
        async with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            console.print(f"[{ts}] [dim]⚙️  {msg}[/dim]")

    def clear(self) -> None:
        console.clear()
