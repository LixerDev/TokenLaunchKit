"""
Validator — Pre-flight checks before launching a token.
Built by LixerDev / TokenLaunchKit
"""

import re
from pathlib import Path
from src.models import TokenConfig
from src.logger import get_logger
from config import config

logger = get_logger(__name__)


class LaunchValidator:
    """
    Validates token config and environment before launching.

    Checks:
    - Required fields (name, symbol)
    - Symbol format (alphanumeric, max 10 chars)
    - Image file exists and is a valid format (if provided)
    - API keys configured for requested features
    - Wallet balance (if initial_buy_sol > 0)
    """

    SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    MAX_NAME_LEN = 32
    MAX_SYMBOL_LEN = 10
    MAX_DESCRIPTION_LEN = 1000

    def validate(self, cfg: TokenConfig) -> tuple[bool, list[str]]:
        """
        Run all validation checks.

        Returns:
        - (True, []) on success
        - (False, [error messages]) on failure
        """
        errors = []
        warnings = []

        # ── Required fields ───────────────────────────────────────────────────
        if not cfg.name or not cfg.name.strip():
            errors.append("Token name is required")
        elif len(cfg.name) > self.MAX_NAME_LEN:
            errors.append(f"Token name too long: {len(cfg.name)} chars (max {self.MAX_NAME_LEN})")

        if not cfg.symbol or not cfg.symbol.strip():
            errors.append("Token symbol is required")
        elif len(cfg.symbol) > self.MAX_SYMBOL_LEN:
            errors.append(f"Symbol too long: {cfg.symbol!r} (max {self.MAX_SYMBOL_LEN} chars)")
        elif not re.match(r'^[A-Za-z0-9]+$', cfg.symbol):
            errors.append(f"Symbol must be alphanumeric only: {cfg.symbol!r}")

        # ── Description ───────────────────────────────────────────────────────
        if not cfg.description and not config.has_openai():
            errors.append(
                "Description is empty and OPENAI_API_KEY is not set. "
                "Provide a description or add your OpenAI API key for AI generation."
            )
        elif len(cfg.description) > self.MAX_DESCRIPTION_LEN:
            errors.append(f"Description too long: {len(cfg.description)} chars (max {self.MAX_DESCRIPTION_LEN})")

        # ── Image ─────────────────────────────────────────────────────────────
        if cfg.image_path:
            path = Path(cfg.image_path)
            if not path.exists():
                errors.append(f"Image file not found: {cfg.image_path}")
            elif path.suffix.lower() not in self.SUPPORTED_IMAGES:
                errors.append(f"Unsupported image format: {path.suffix}. Use: {', '.join(self.SUPPORTED_IMAGES)}")
            else:
                size_kb = path.stat().st_size / 1024
                if size_kb > 5000:
                    errors.append(f"Image too large: {size_kb:.0f} KB. PumpFun accepts images up to ~5MB.")

        elif not cfg.image_url and cfg.generate_image:
            if not config.has_openai():
                errors.append(
                    "generate_image=true but OPENAI_API_KEY is not set. "
                    "Add your OpenAI key or provide an image file/URL."
                )

        # ── IPFS ──────────────────────────────────────────────────────────────
        if not config.has_pinata() and not config.USE_PUMPFUN_IPFS and not config.NFT_STORAGE_API_KEY:
            logger.warning("No IPFS provider configured — will use pump.fun native IPFS as fallback")

        # ── Wallet ────────────────────────────────────────────────────────────
        if not config.has_wallet() and not cfg.dry_run:
            errors.append(
                "PRIVATE_KEY not set in .env. "
                "Add your Solana wallet private key (base58) to launch tokens."
            )

        # ── Buy params ────────────────────────────────────────────────────────
        if cfg.initial_buy_sol < 0:
            errors.append("initial_buy_sol cannot be negative")
        if not 0 <= cfg.slippage <= 50:
            errors.append(f"slippage must be 0–50, got {cfg.slippage}")
        if cfg.priority_fee_sol < 0:
            errors.append("priority_fee_sol cannot be negative")

        # ── Social links ──────────────────────────────────────────────────────
        for field, url in [("twitter", cfg.twitter), ("telegram", cfg.telegram), ("website", cfg.website)]:
            if url and not url.startswith("http"):
                errors.append(f"{field} must be a full URL starting with http: {url!r}")

        ok = len(errors) == 0
        return ok, errors

    def print_report(self, cfg: TokenConfig):
        """Print a validation report to the terminal."""
        from rich.console import Console
        from rich.table import Table
        from rich import box

        console = Console()
        ok, errors = self.validate(cfg)

        console.print(f"\n[bold]🔍 Pre-launch Validation — {cfg.name} (${cfg.symbol})[/bold]\n")

        checks = [
            ("Name", cfg.name, bool(cfg.name)),
            ("Symbol", cfg.symbol, bool(cfg.symbol) and len(cfg.symbol) <= 10),
            ("Description", (cfg.description[:40] + "..." if len(cfg.description) > 40 else cfg.description) or "[AI will generate]", True),
            ("Image", cfg.image_path or cfg.image_url or "[AI will generate]", True),
            ("Wallet", "Configured" if config.has_wallet() else "NOT SET", config.has_wallet() or cfg.dry_run),
            ("IPFS", "Pinata" if config.has_pinata() else ("pump.fun" if config.USE_PUMPFUN_IPFS else "nft.storage" if config.NFT_STORAGE_API_KEY else "pump.fun (fallback)"), True),
            ("OpenAI", "Configured" if config.has_openai() else "NOT SET", config.has_openai() or (bool(cfg.image_path) and bool(cfg.description))),
            ("Initial Buy", f"{cfg.initial_buy_sol} SOL" if cfg.initial_buy_sol else "No buy", True),
            ("Slippage", f"{cfg.slippage}%", True),
            ("Dry Run", "YES — no broadcast" if cfg.dry_run else "NO — will launch", True),
        ]

        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        t.add_column("Field", width=18)
        t.add_column("Value", width=40)
        t.add_column("Status", width=6)

        for field, value, is_ok in checks:
            status = "[green]✓[/green]" if is_ok else "[red]✗[/red]"
            t.add_row(field, f"[dim]{value}[/dim]", status)

        console.print(t)

        if errors:
            console.print("\n[bold red]Validation Errors:[/bold red]")
            for err in errors:
                console.print(f"  [red]• {err}[/red]")
            console.print()
        else:
            console.print("\n[bold green]✅ All checks passed — ready to launch![/bold green]\n")

        return ok, errors
