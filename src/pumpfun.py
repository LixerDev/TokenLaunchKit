"""
PumpFun Launcher — Create tokens on PumpFun's bonding curve.

Flow:
1. Generate a new mint keypair (the token address)
2. Call PumpPortal API to create the token (submits on-chain tx)
3. Optionally place an initial buy order

PumpPortal API Docs: https://pumpportal.fun/api/

Built by LixerDev / TokenLaunchKit
"""

import json
import requests
import base58
from src.models import TokenConfig, PumpFunResult
from src.logger import get_logger
from config import config

logger = get_logger(__name__)

PUMPPORTAL_CREATE_URL = "https://pumpportal.fun/api/trade"
PUMPFUN_PROGRAM_ID    = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

# PumpFun token constants
TOTAL_SUPPLY           = 1_000_000_000   # 1B tokens
DECIMALS               = 6
INITIAL_VIRTUAL_SOL    = 30              # SOL in bonding curve at launch
INITIAL_VIRTUAL_TOKENS = 1_073_000_000  # virtual token reserve


class PumpFunLauncher:
    """
    Launch tokens on PumpFun using the PumpPortal lightning API.

    The PumpPortal API handles:
    - On-chain "create" instruction to PumpFun program
    - Signing via your provided private key
    - Optional bundled initial buy
    """

    def launch(
        self,
        token_cfg: TokenConfig,
        metadata_uri: str,
        dry_run: bool = False,
    ) -> PumpFunResult:
        """
        Create a new PumpFun token.

        Parameters:
        - token_cfg: TokenConfig with name, symbol, socials, buy params
        - metadata_uri: IPFS/HTTP URI to the token metadata JSON
        - dry_run: If True, generate mint keypair but skip actual broadcast

        Returns:
        - PumpFunResult with mint address, bonding curve, transaction sig

        Raises:
        - ValueError: If private key not configured
        - RuntimeError: If API call fails
        """
        if not config.has_wallet() and not dry_run:
            raise ValueError("PRIVATE_KEY not set. Add your Solana wallet private key to .env")

        # Generate a fresh mint keypair
        mint_keypair = self._generate_keypair()
        mint_pubkey  = mint_keypair["publicKey"]

        logger.info(f"Mint address: {mint_pubkey}")
        logger.info(f"Metadata URI: {metadata_uri}")

        if dry_run:
            logger.info("[DRY RUN] Skipping PumpFun broadcast")
            return self._dry_run_result(mint_pubkey, token_cfg)

        return self._broadcast(token_cfg, mint_keypair, metadata_uri)

    def _broadcast(self, cfg: TokenConfig, mint_kp: dict, metadata_uri: str) -> PumpFunResult:
        """Send the create transaction via PumpPortal API."""

        # Build request payload
        payload = {
            "action": "create",
            "tokenMetadata": {
                "name": cfg.name,
                "symbol": cfg.symbol,
                "uri": metadata_uri,
            },
            "mint": mint_kp["privateKeyBase58"],      # PumpPortal signs with this
            "denominatedInSol": "true",
            "amount": str(cfg.initial_buy_sol) if cfg.initial_buy_sol > 0 else "0",
            "slippage": cfg.slippage,
            "priorityFee": cfg.priority_fee_sol,
            "pool": "pump",
        }

        headers = {"Content-Type": "application/json"}
        if config.PUMPPORTAL_API_KEY:
            url = f"{PUMPPORTAL_CREATE_URL}?api-key={config.PUMPPORTAL_API_KEY}"
        else:
            url = PUMPPORTAL_CREATE_URL

        logger.info(f"Broadcasting to PumpPortal...")

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except requests.HTTPError as e:
            body = e.response.text if e.response else "no response"
            raise RuntimeError(f"PumpPortal API error {e.response.status_code}: {body}") from e
        except Exception as e:
            raise RuntimeError(f"PumpPortal request failed: {e}") from e

        tx_sig = data.get("signature", data.get("tx", ""))
        mint   = mint_kp["publicKey"]

        if not tx_sig:
            raise RuntimeError(f"PumpPortal returned no transaction signature: {data}")

        result = PumpFunResult(
            mint=mint,
            transaction_signature=tx_sig,
            pumpfun_url=f"{config.PUMPFUN_URL}/{mint}",
            dexscreener_url=f"{config.DEXSCREENER_URL}/{mint}",
            solana_explorer_url=f"{config.SOLANA_EXPLORER}/tx/{tx_sig}",
        )

        logger.info(f"Token created! Mint: {mint}")
        logger.info(f"TX: {tx_sig}")

        return result

    def get_bonding_curve(self, mint: str) -> dict | None:
        """
        Fetch current bonding curve state for a token from PumpFun API.
        Returns None if token not found.
        """
        try:
            resp = requests.get(
                f"https://frontend-api.pump.fun/coins/{mint}",
                timeout=15,
                headers={"User-Agent": "TokenLaunchKit/1.0"}
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            logger.warning(f"Could not fetch bonding curve: {e}")
            return None

    def check_status(self, mint: str) -> dict:
        """
        Check if a token is live on PumpFun.

        Returns dict with:
        - exists: bool
        - migrated: bool (migrated to Raydium)
        - market_cap_usd: float
        - price_usd: float
        """
        data = self.get_bonding_curve(mint)
        if not data:
            return {"exists": False, "mint": mint}

        return {
            "exists": True,
            "mint": mint,
            "name": data.get("name", ""),
            "symbol": data.get("symbol", ""),
            "market_cap_usd": data.get("usd_market_cap", 0),
            "price_usd": data.get("price", 0),
            "migrated": data.get("raydium_pool") is not None,
            "virtual_sol_reserves": data.get("virtual_sol_reserves", 0),
            "virtual_token_reserves": data.get("virtual_token_reserves", 0),
            "bonding_curve": data.get("bonding_curve", ""),
            "created_timestamp": data.get("created_timestamp", 0),
        }

    def _generate_keypair(self) -> dict:
        """
        Generate a Solana keypair and return public + private keys.

        In production: uses solders or nacl for real Ed25519 keypair generation.
        This implementation uses nacl via PyNaCl.
        """
        try:
            from nacl.signing import SigningKey
            import base58

            signing_key = SigningKey.generate()
            private_key_bytes = bytes(signing_key)
            public_key_bytes  = bytes(signing_key.verify_key)

            # Solana private key = 64 bytes (privkey + pubkey)
            full_private = private_key_bytes + public_key_bytes

            return {
                "publicKey": base58.b58encode(public_key_bytes).decode(),
                "privateKeyBase58": base58.b58encode(full_private).decode(),
                "privateKeyBytes": list(full_private),
            }
        except ImportError:
            # Fallback: generate using os.urandom (less secure, OK for demo)
            import os
            import hashlib
            seed = os.urandom(32)
            # Simplified keypair (not cryptographically valid Ed25519)
            # In production, always use PyNaCl or solders
            pubkey_bytes = hashlib.sha256(seed).digest()
            import base58
            return {
                "publicKey": base58.b58encode(pubkey_bytes).decode(),
                "privateKeyBase58": base58.b58encode(seed + pubkey_bytes).decode(),
                "privateKeyBytes": list(seed + pubkey_bytes),
            }

    def _dry_run_result(self, mint: str, cfg: TokenConfig) -> PumpFunResult:
        return PumpFunResult(
            mint=mint,
            transaction_signature="DRY_RUN_NO_BROADCAST",
            pumpfun_url=f"{config.PUMPFUN_URL}/{mint}",
            dexscreener_url=f"{config.DEXSCREENER_URL}/{mint}",
            solana_explorer_url=f"{config.SOLANA_EXPLORER}/address/{mint}",
        )
