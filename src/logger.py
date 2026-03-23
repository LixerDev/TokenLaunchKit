import logging
from rich.console import Console
from rich.logging import RichHandler
from config import config

console = Console()

def get_logger(name: str) -> logging.Logger:
    handlers = [RichHandler(console=console, rich_tracebacks=True, show_path=False, markup=True)]
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL, logging.INFO), handlers=handlers, format="%(message)s", datefmt="[%H:%M:%S]")
    return logging.getLogger(name)

def print_banner():
    console.print("""
[bold magenta]
  ████████╗ ██████╗ ██╗  ██╗███████╗███╗   ██╗
     ██╔══╝██╔═══██╗██║ ██╔╝██╔════╝████╗  ██║
     ██║   ██║   ██║█████╔╝ █████╗  ██╔██╗ ██║
     ██║   ██║   ██║██╔═██╗ ██╔══╝  ██║╚██╗██║
     ██║   ╚██████╔╝██║  ██╗███████╗██║ ╚████║
     ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝
  [/bold magenta][bold white]  ██╗      █████╗ ██╗   ██╗███╗   ██╗ ██████╗██╗  ██╗██╗  ██╗██╗████████╗
     ██║     ██╔══██╗██║   ██║████╗  ██║██╔════╝██║  ██║██║ ██╔╝██║╚══██╔══╝
     ██║     ███████║██║   ██║██╔██╗ ██║██║     ███████║█████╔╝ ██║   ██║
     ██║     ██╔══██║██║   ██║██║╚██╗██║██║     ██╔══██║██╔═██╗ ██║   ██║
     ███████╗██║  ██║╚██████╔╝██║ ╚████║╚██████╗██║  ██║██║  ██╗██║   ██║
     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝[/bold white]
[dim]  Metadata • IPFS • PumpFun • Landing Page | Built by LixerDev | v1.0.0[/dim]
""")

def print_success_summary(result):
    console.print("\n")
    console.rule("[bold green]🚀 Token Launched Successfully![/bold green]")
    console.print()
    if result.pumpfun:
        console.print(f"  [bold]Mint:[/bold]       [cyan]{result.pumpfun.mint}[/cyan]")
        console.print(f"  [bold]PumpFun:[/bold]    [link={result.pumpfun.pumpfun_url}]{result.pumpfun.pumpfun_url}[/link]")
        console.print(f"  [bold]Dexscreener:[/bold] [link={result.pumpfun.dexscreener_url}]{result.pumpfun.dexscreener_url}[/link]")
        console.print(f"  [bold]Transaction:[/bold] [link={result.pumpfun.solana_explorer_url}]{result.pumpfun.transaction_signature[:32]}...[/link]")
    if result.ipfs:
        console.print(f"  [bold]Metadata:[/bold]   [dim]{result.ipfs.metadata_uri[:60]}...[/dim]")
    if result.landing_page_path:
        console.print(f"  [bold]Landing:[/bold]    {result.landing_page_path}")
    if result.receipt_path:
        console.print(f"  [bold]Receipt:[/bold]    {result.receipt_path}")
    console.print()
