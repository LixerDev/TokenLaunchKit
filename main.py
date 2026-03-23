#!/usr/bin/env python3
"""
TokenLaunchKit — End-to-end Solana token launcher.
Metadata → IPFS → PumpFun → Landing Page.
Built by LixerDev
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from config import config
from src.logger import get_logger, print_banner, print_success_summary
from src.models import TokenConfig, LaunchResult, IpfsResult, PumpFunResult
from src.validator import LaunchValidator
from src.metadata import MetadataGenerator
from src.image import ImageGenerator
from src.ipfs import IpfsUploader
from src.pumpfun import PumpFunLauncher
from src.landing import LandingPageGenerator

app     = typer.Typer(help="TokenLaunchKit — launch Solana tokens end-to-end", no_args_is_help=True)
console = Console()
logger  = get_logger(__name__)


# ─── launch ───────────────────────────────────────────────────────────────────

@app.command()
def launch(
    name:          Optional[str]   = typer.Option(None,   "--name",        "-n",  help="Token name"),
    symbol:        Optional[str]   = typer.Option(None,   "--symbol",      "-s",  help="Token symbol (e.g. GSOL)"),
    description:   str             = typer.Option("",     "--description", "-d",  help="Token description (AI-generated if empty)"),
    image:         Optional[str]   = typer.Option(None,   "--image",       "-i",  help="Path to logo image (AI-generated if omitted)"),
    twitter:       str             = typer.Option("",     "--twitter",           help="Twitter URL"),
    telegram:      str             = typer.Option("",     "--telegram",          help="Telegram URL"),
    website:       str             = typer.Option("",     "--website",           help="Website URL"),
    initial_buy:   float           = typer.Option(0.0,    "--initial-buy",       help="Initial SOL buy on launch"),
    slippage:      int             = typer.Option(10,     "--slippage",          help="Slippage % (default: 10)"),
    priority_fee:  float           = typer.Option(0.0005, "--priority-fee",      help="Priority fee in SOL"),
    image_style:   str             = typer.Option("vibrant", "--image-style",    help="AI image style: vibrant|cartoon|pixel|minimal|retro"),
    vibe:          str             = typer.Option("",     "--vibe",              help="Vibe hint for AI (e.g. 'bullish memecoin')"),
    cfg_file:      Optional[str]   = typer.Option(None,   "--config",      "-c",  help="Load config from JSON file"),
    output:        Optional[str]   = typer.Option(None,   "--output",      "-o",  help="Output directory"),
    dry_run:       bool            = typer.Option(False,  "--dry-run",           help="Generate everything but skip launch"),
):
    """
    Full pipeline: metadata → AI image → IPFS → PumpFun → landing page.

    Examples:
      python main.py launch --name "GigaSOL" --symbol "GSOL"
      python main.py launch --config examples/my_token.json
      python main.py launch --name "GigaSOL" --symbol "GSOL" --dry-run
    """
    print_banner()

    # Load config
    if cfg_file:
        cfg = TokenConfig.from_json(cfg_file)
        if dry_run: cfg.dry_run = True
    else:
        if not name:
            console.print("[red]--name is required (or use --config)[/red]")
            raise typer.Exit(1)
        if not symbol:
            console.print("[red]--symbol is required (or use --config)[/red]")
            raise typer.Exit(1)
        cfg = TokenConfig(
            name=name, symbol=symbol.upper(), description=description,
            image_path=image, twitter=twitter, telegram=telegram, website=website,
            initial_buy_sol=initial_buy, slippage=slippage, priority_fee_sol=priority_fee,
            generate_image=(image is None), image_style=image_style, dry_run=dry_run,
        )

    out_dir = output or str(Path(config.OUTPUT_DIR) / cfg.name.lower().replace(" ", "_"))
    result  = _run_pipeline(cfg, out_dir, vibe)
    print_success_summary(result)

    receipt_path = str(Path(out_dir) / "receipt.json")
    result.receipt_path = receipt_path
    result.save(receipt_path)
    console.print(f"  [dim]Receipt saved: {receipt_path}[/dim]\n")


# ─── generate ─────────────────────────────────────────────────────────────────

@app.command()
def generate(
    name:   str = typer.Argument(..., help="Token name"),
    symbol: str = typer.Option("",  "--symbol", "-s"),
    vibe:   str = typer.Option("",  "--vibe",   help="Theme/vibe for the token"),
    count:  int = typer.Option(5,   "--count",  help="Number of name suggestions"),
):
    """
    Generate AI metadata: descriptions, name suggestions, image prompts.

    Examples:
      python main.py generate "GigaSOL" --vibe "bullish memecoin"
      python main.py generate "ideas" --vibe "cat token on solana" --count 8
    """
    print_banner()
    meta = MetadataGenerator()

    if name.lower() == "ideas" or not symbol:
        console.print(f"\n[bold]🤖 Generating {count} name suggestions for: [cyan]{vibe or name}[/cyan][/bold]\n")
        suggestions = meta.suggest_names(vibe or name, count)
        for i, s in enumerate(suggestions, 1):
            console.print(f"  [bold cyan]{i}. {s.get('name', '')}[/bold cyan] (${s.get('symbol', '')}) — {s.get('tagline', '')}")
        console.print()
        return

    console.print(f"\n[bold]🤖 Generating metadata for [cyan]{name}[/cyan] (${symbol.upper()})[/bold]\n")

    desc = meta.generate_description(name, symbol, vibe)
    console.print(f"[bold]Description:[/bold]\n  {desc}\n")

    img_prompt = meta.generate_image_prompt(name, desc, config.IMAGE_STYLE)
    console.print(f"[bold]Image Prompt:[/bold]\n  {img_prompt[:200]}...\n")


# ─── image ────────────────────────────────────────────────────────────────────

@app.command()
def image(
    name:    str = typer.Argument(..., help="Token name"),
    style:   str = typer.Option("vibrant", "--style", "-s", help="Image style: vibrant|cartoon|pixel|minimal|retro"),
    output:  str = typer.Option("./output/logo.png", "--output", "-o"),
    prompt:  str = typer.Option("", "--prompt", help="Custom DALL-E prompt (overrides AI-generated)"),
):
    """Generate an AI token logo using DALL-E 3."""
    print_banner()
    meta = MetadataGenerator()
    img  = ImageGenerator()

    description = f"A {style} Solana memecoin called {name}"
    dall_e_prompt = prompt or meta.generate_image_prompt(name, description, style)

    console.print(f"\n[bold]🎨 Generating logo for [cyan]{name}[/cyan] (style: {style})[/bold]")
    console.print(f"[dim]Prompt: {dall_e_prompt[:100]}...[/dim]\n")

    path = img.generate_ai_logo(dall_e_prompt, output)
    console.print(f"[green]✅ Logo saved: {path}[/green]")


# ─── upload ───────────────────────────────────────────────────────────────────

@app.command()
def upload(
    image_file:  str = typer.Argument(..., help="Path to image file"),
    name:        str = typer.Option(..., "--name",   "-n"),
    symbol:      str = typer.Option(..., "--symbol", "-s"),
    description: str = typer.Option("", "--description", "-d"),
    twitter:     str = typer.Option("", "--twitter"),
    telegram:    str = typer.Option("", "--telegram"),
    website:     str = typer.Option("", "--website"),
):
    """Upload image + metadata to IPFS and print the metadata URI."""
    print_banner()
    uploader = IpfsUploader()

    console.print(f"\n[bold]📤 Uploading to IPFS...[/bold]")
    result = uploader.upload(
        image_path=image_file, name=name, symbol=symbol, description=description,
        twitter=twitter, telegram=telegram, website=website,
    )

    console.print(f"\n[green]✅ Upload complete! Provider: {result.provider}[/green]")
    console.print(f"  [bold]Image URL:[/bold]    {result.image_url or result.image_gateway_url}")
    console.print(f"  [bold]Metadata URI:[/bold] {result.metadata_uri}\n")


# ─── page ─────────────────────────────────────────────────────────────────────

@app.command()
def page(
    mint:        str           = typer.Argument(..., help="Token mint address"),
    name:        str           = typer.Option(..., "--name",   "-n"),
    symbol:      str           = typer.Option(..., "--symbol", "-s"),
    description: str           = typer.Option("", "--description", "-d"),
    image_url:   str           = typer.Option("", "--image-url"),
    twitter:     str           = typer.Option("", "--twitter"),
    telegram:    str           = typer.Option("", "--telegram"),
    website:     str           = typer.Option("", "--website"),
    output:      str           = typer.Option("./output/index.html", "--output", "-o"),
):
    """Generate a token landing page for a deployed token."""
    print_banner()
    gen = LandingPageGenerator()
    path = gen.generate(
        output_path=output, name=name, symbol=symbol, description=description,
        mint=mint, image_url=image_url, twitter=twitter, telegram=telegram,
        website=website,
    )
    console.print(f"\n[green]✅ Landing page: {path}[/green]")
    console.print(f"  Open in browser: [link=file://{Path(path).resolve()}]file://{path}[/link]\n")


# ─── validate ─────────────────────────────────────────────────────────────────

@app.command()
def validate(
    cfg_file: Optional[str] = typer.Option(None, "--config", "-c"),
    name:     Optional[str] = typer.Option(None, "--name",   "-n"),
    symbol:   Optional[str] = typer.Option(None, "--symbol", "-s"),
):
    """Validate a token config without launching."""
    print_banner()

    if cfg_file:
        cfg = TokenConfig.from_json(cfg_file)
    elif name and symbol:
        cfg = TokenConfig(name=name, symbol=symbol, dry_run=True)
    else:
        console.print("[red]Provide --config or --name + --symbol[/red]")
        raise typer.Exit(1)

    validator = LaunchValidator()
    ok, errors = validator.print_report(cfg)
    raise typer.Exit(0 if ok else 1)


# ─── Pipeline ─────────────────────────────────────────────────────────────────

def _run_pipeline(cfg: TokenConfig, out_dir: str, vibe: str = "") -> LaunchResult:
    """Run the full launch pipeline."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    result = LaunchResult(launched_at=datetime.now(timezone.utc).isoformat())

    validator = LaunchValidator()
    ok, errors = validator.print_report(cfg)
    if not ok:
        console.print("[red]Fix the errors above before launching.[/red]")
        raise typer.Exit(1)

    # ── Step 1: Generate description ─────────────────────────────────────────
    if not cfg.description:
        console.print("[dim]Step 1/5: Generating description with GPT-4o...[/dim]")
        meta = MetadataGenerator()
        cfg.description = meta.generate_description(cfg.name, cfg.symbol, vibe)
        console.print(f"  [dim]{cfg.description[:80]}...[/dim]")

    # ── Step 2: Generate / process image ─────────────────────────────────────
    image_path = cfg.image_path
    if not image_path:
        img_gen = ImageGenerator()
        logo_path = str(Path(out_dir) / "logo.png")

        if cfg.image_url:
            console.print("[dim]Step 2/5: Downloading image...[/dim]")
            image_path = img_gen.download_image(cfg.image_url, logo_path)
        elif cfg.generate_image:
            console.print("[dim]Step 2/5: Generating AI logo with DALL-E 3...[/dim]")
            meta = MetadataGenerator()
            prompt = meta.generate_image_prompt(cfg.name, cfg.description, cfg.image_style)
            image_path = img_gen.generate_ai_logo(prompt, logo_path)
        else:
            console.print("[yellow]⚠️  No image — skipping image upload[/yellow]")
    else:
        console.print("[dim]Step 2/5: Processing local image...[/dim]")
        img_gen = ImageGenerator()
        image_path = img_gen.process_local_image(image_path, str(Path(out_dir) / "logo.png"))

    # ── Step 3: Upload to IPFS ────────────────────────────────────────────────
    console.print("[dim]Step 3/5: Uploading to IPFS...[/dim]")
    uploader = IpfsUploader()
    ipfs_result = uploader.upload(
        image_path=image_path or "",
        name=cfg.name, symbol=cfg.symbol, description=cfg.description,
        twitter=cfg.twitter, telegram=cfg.telegram, website=cfg.website,
    ) if image_path else IpfsResult(metadata_uri="", provider="none")
    result.ipfs = ipfs_result
    console.print(f"  IPFS: {ipfs_result.provider} — {ipfs_result.metadata_uri[:60] if ipfs_result.metadata_uri else 'N/A'}...")

    # ── Step 4: Launch on PumpFun ─────────────────────────────────────────────
    console.print("[dim]Step 4/5: Launching on PumpFun...[/dim]")
    launcher = PumpFunLauncher()
    pumpfun_result = launcher.launch(cfg, ipfs_result.metadata_uri or "", cfg.dry_run)
    result.pumpfun = pumpfun_result
    result.token = {
        "name": cfg.name, "symbol": cfg.symbol,
        "mint": pumpfun_result.mint,
        "decimals": 6, "total_supply": 1_000_000_000,
    }

    # ── Step 5: Generate landing page ─────────────────────────────────────────
    if cfg.generate_landing:
        console.print("[dim]Step 5/5: Generating landing page...[/dim]")
        gen = LandingPageGenerator()
        page_path = gen.generate(
            output_path=str(Path(out_dir) / "index.html"),
            name=cfg.name, symbol=cfg.symbol, description=cfg.description,
            mint=pumpfun_result.mint,
            image_url=ipfs_result.image_gateway_url or ipfs_result.image_url,
            twitter=cfg.twitter, telegram=cfg.telegram, website=cfg.website,
            pumpfun_url=pumpfun_result.pumpfun_url,
            dexscreener_url=pumpfun_result.dexscreener_url,
        )
        result.landing_page_path = page_path

    result.status = "dry_run" if cfg.dry_run else "success"
    return result


if __name__ == "__main__":
    app()
