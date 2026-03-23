"""
Models — Data structures for TokenLaunchKit.
Built by LixerDev
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import json


@dataclass
class TokenConfig:
    """Complete token configuration for a launch."""
    name: str
    symbol: str
    description: str = ""
    image_path: Optional[str] = None     # Local file path
    image_url: Optional[str] = None      # Remote URL
    twitter: str = ""
    telegram: str = ""
    website: str = ""
    initial_buy_sol: float = 0.0
    slippage: int = 10
    priority_fee_sol: float = 0.0005
    generate_image: bool = True          # Use DALL-E 3 if no image provided
    generate_landing: bool = True
    image_style: str = "vibrant"         # vibrant | cartoon | pixel | realistic | minimal
    dry_run: bool = False

    @classmethod
    def from_json(cls, path: str) -> "TokenConfig":
        with open(path) as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self, path: str):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def validate(self) -> list[str]:
        errors = []
        if not self.name:
            errors.append("name is required")
        if not self.symbol:
            errors.append("symbol is required")
        if len(self.symbol) > 10:
            errors.append(f"symbol too long: {self.symbol!r} (max 10 chars)")
        if self.initial_buy_sol < 0:
            errors.append("initial_buy_sol cannot be negative")
        if not 0 <= self.slippage <= 50:
            errors.append(f"slippage must be 0–50, got {self.slippage}")
        if not self.image_path and not self.image_url and not self.generate_image:
            errors.append("provide image_path, image_url, or set generate_image=true")
        return errors


@dataclass
class IpfsResult:
    image_cid: str = ""
    image_url: str = ""                  # ipfs://...
    image_gateway_url: str = ""          # https://gateway.pinata.cloud/ipfs/...
    metadata_cid: str = ""
    metadata_url: str = ""               # ipfs://...
    metadata_uri: str = ""               # https gateway URL (used by PumpFun)
    provider: str = ""                   # "pinata" | "pumpfun" | "nftstorage"


@dataclass
class PumpFunResult:
    mint: str = ""
    bonding_curve: str = ""
    transaction_signature: str = ""
    pumpfun_url: str = ""
    dexscreener_url: str = ""
    solana_explorer_url: str = ""
    initial_buy_tx: str = ""


@dataclass
class LaunchResult:
    status: str = "pending"              # pending | success | failed | dry_run
    token: dict = field(default_factory=dict)
    ipfs: Optional[IpfsResult] = None
    pumpfun: Optional[PumpFunResult] = None
    landing_page_path: str = ""
    receipt_path: str = ""
    launched_at: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "token": self.token,
            "ipfs": {
                "image_url": self.ipfs.image_url if self.ipfs else "",
                "image_gateway_url": self.ipfs.image_gateway_url if self.ipfs else "",
                "metadata_url": self.ipfs.metadata_url if self.ipfs else "",
                "metadata_uri": self.ipfs.metadata_uri if self.ipfs else "",
                "provider": self.ipfs.provider if self.ipfs else "",
            } if self.ipfs else {},
            "pumpfun": {
                "mint": self.pumpfun.mint if self.pumpfun else "",
                "bonding_curve": self.pumpfun.bonding_curve if self.pumpfun else "",
                "transaction": self.pumpfun.transaction_signature if self.pumpfun else "",
                "pumpfun_url": self.pumpfun.pumpfun_url if self.pumpfun else "",
                "dexscreener_url": self.pumpfun.dexscreener_url if self.pumpfun else "",
                "solana_explorer_url": self.pumpfun.solana_explorer_url if self.pumpfun else "",
            } if self.pumpfun else {},
            "landing_page": self.landing_page_path,
            "receipt": self.receipt_path,
            "launched_at": self.launched_at,
            "error": self.error,
        }

    def save(self, path: str):
        import json
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
