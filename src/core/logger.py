from rich.console import Console
from rich.progress import Progress
from rich.traceback import install

console = Console()
install(show_locals=False)


def info(msg: str):
    console.log(f"[bold cyan]INFO[/]: {msg}")


def warn(msg: str):
    console.log(f"[bold yellow]WARN[/]: {msg}")


def error(msg: str):
    console.log(f"[bold red]ERROR[/]: {msg}")


def success(msg: str):
    console.log(f"[bold green]OK[/]: {msg}")


class Step:
    def __init__(self, title: str):
        self.title = title
        info(f"➡️ {title}")

    def done(self, extra: str = ""):
        success(f"✔ {self.title} {extra}")

