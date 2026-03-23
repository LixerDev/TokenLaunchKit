"""
IPFS Uploader — Upload token images and metadata to IPFS.

Supported providers:
1. Pinata (primary) — requires PINATA_JWT
2. pump.fun native IPFS — no key needed (USE_PUMPFUN_IPFS=true)
3. nft.storage (fallback) — requires NFT_STORAGE_API_KEY

Built by LixerDev / TokenLaunchKit
"""

import json
import requests
from pathlib import Path
from src.models import IpfsResult
from src.logger import get_logger
from config import config

logger = get_logger(__name__)


class PinataUploader:
    """Upload files and JSON to Pinata IPFS."""

    def __init__(self, jwt: str):
        self.jwt = jwt
        self.headers = {"Authorization": f"Bearer {jwt}"}

    def upload_file(self, file_path: str, name: str = "") -> str:
        """
        Upload a file to Pinata.

        Returns:
        - str: IPFS CID (e.g. "bafybeig...")
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Uploading {path.name} to Pinata...")

        with open(file_path, "rb") as f:
            files = {
                "file": (name or path.name, f, self._mime_type(path.suffix)),
            }
            data = {
                "pinataMetadata": json.dumps({"name": name or path.stem}),
                "pinataOptions": json.dumps({"cidVersion": 1}),
            }
            resp = requests.post(
                config.PINATA_UPLOAD_URL,
                headers=self.headers,
                files=files,
                data=data,
                timeout=60,
            )
            resp.raise_for_status()
            cid = resp.json()["IpfsHash"]
            logger.info(f"Pinata upload OK: {cid}")
            return cid

    def upload_json(self, data: dict, name: str = "metadata") -> str:
        """
        Upload a JSON object to Pinata.

        Returns:
        - str: IPFS CID
        """
        logger.info(f"Uploading metadata JSON to Pinata...")
        payload = {
            "pinataContent": data,
            "pinataMetadata": {"name": name},
            "pinataOptions": {"cidVersion": 1},
        }
        resp = requests.post(
            config.PINATA_JSON_URL,
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        cid = resp.json()["IpfsHash"]
        logger.info(f"Pinata metadata upload OK: {cid}")
        return cid

    def _mime_type(self, suffix: str) -> str:
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(suffix.lower(), "application/octet-stream")


class PumpFunIpfsUploader:
    """
    Use pump.fun's native IPFS endpoint.

    No API key required — pump.fun hosts this for all token creators.
    Returns a metadataUri that pump.fun accepts directly.

    POST https://pump.fun/api/ipfs
    Form fields: name, symbol, description, twitter, telegram, website, showName, file (image)
    """

    def upload(
        self,
        image_path: str,
        name: str,
        symbol: str,
        description: str,
        twitter: str = "",
        telegram: str = "",
        website: str = "",
    ) -> tuple[str, str]:
        """
        Upload metadata + image to pump.fun IPFS in one request.

        Returns:
        - tuple: (metadataUri, imageUrl) — the URI pump.fun accepts
        """
        logger.info(f"Uploading to pump.fun IPFS...")

        with open(image_path, "rb") as img_file:
            suffix = Path(image_path).suffix.lower()
            mime = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif"}.get(suffix.lstrip("."), "image/png")

            files = {"file": (Path(image_path).name, img_file, mime)}
            data = {
                "name": name,
                "symbol": symbol,
                "description": description,
                "twitter": twitter,
                "telegram": telegram,
                "website": website,
                "showName": "true",
            }

            headers = {
                "Accept": "application/json",
                "Origin": "https://pump.fun",
                "Referer": "https://pump.fun/",
            }

            resp = requests.post(
                config.PUMPFUN_IPFS_URL,
                files=files,
                data=data,
                headers=headers,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
            metadata_uri = result.get("metadataUri", "")
            image_url = result.get("image", "")
            logger.info(f"pump.fun IPFS upload OK: {metadata_uri}")
            return metadata_uri, image_url


class NftStorageUploader:
    """Upload to nft.storage (IPFS via Filecoin)."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def upload_file(self, file_path: str) -> str:
        """Upload a file and return its CID."""
        with open(file_path, "rb") as f:
            resp = requests.post(
                config.NFT_STORAGE_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                data=f,
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["value"]["cid"]


class IpfsUploader:
    """
    Unified IPFS uploader — auto-selects provider based on config.

    Priority:
    1. pump.fun native IPFS (if USE_PUMPFUN_IPFS=true)
    2. Pinata (if PINATA_JWT set)
    3. nft.storage (if NFT_STORAGE_API_KEY set)
    """

    def upload(
        self,
        image_path: str,
        name: str,
        symbol: str,
        description: str,
        twitter: str = "",
        telegram: str = "",
        website: str = "",
        creator_address: str = "",
    ) -> IpfsResult:
        """
        Upload image + metadata to IPFS and return all URLs.

        Returns:
        - IpfsResult with image_url, metadata_url, metadata_uri
        """
        result = IpfsResult()

        # ── Strategy 1: pump.fun native IPFS ─────────────────────────────────
        if config.USE_PUMPFUN_IPFS:
            return self._upload_via_pumpfun(image_path, name, symbol, description, twitter, telegram, website)

        # ── Strategy 2: Pinata ───────────────────────────────────────────────
        if config.has_pinata():
            return self._upload_via_pinata(image_path, name, symbol, description, twitter, telegram, website, creator_address)

        # ── Strategy 3: nft.storage ──────────────────────────────────────────
        if config.NFT_STORAGE_API_KEY:
            return self._upload_via_nft_storage(image_path, name, symbol, description, twitter, telegram, website, creator_address)

        # ── Fallback: pump.fun IPFS ───────────────────────────────────────────
        logger.warning("No IPFS keys configured — using pump.fun native IPFS")
        return self._upload_via_pumpfun(image_path, name, symbol, description, twitter, telegram, website)

    def _upload_via_pumpfun(self, image_path, name, symbol, description, twitter, telegram, website) -> IpfsResult:
        uploader = PumpFunIpfsUploader()
        metadata_uri, image_url = uploader.upload(image_path, name, symbol, description, twitter, telegram, website)
        return IpfsResult(
            image_url=image_url,
            image_gateway_url=image_url,
            metadata_uri=metadata_uri,
            metadata_url=metadata_uri,
            provider="pumpfun",
        )

    def _upload_via_pinata(self, image_path, name, symbol, description, twitter, telegram, website, creator_address) -> IpfsResult:
        pinata = PinataUploader(config.PINATA_JWT)

        # Upload image
        image_cid = pinata.upload_file(image_path, f"{name}-logo")
        image_ipfs = f"ipfs://{image_cid}"
        image_gateway = f"{config.PINATA_GATEWAY}/{image_cid}"

        # Build metadata
        from src.metadata import MetadataGenerator
        meta_gen = MetadataGenerator()
        metadata = meta_gen.build_metaplex_metadata(
            name=name, symbol=symbol, description=description,
            image_url=image_ipfs, website=website, twitter=twitter,
            telegram=telegram, creator_address=creator_address,
        )

        # Upload metadata
        meta_cid = pinata.upload_json(metadata, f"{name}-metadata")
        meta_ipfs = f"ipfs://{meta_cid}"
        meta_gateway = f"{config.PINATA_GATEWAY}/{meta_cid}"

        return IpfsResult(
            image_cid=image_cid, image_url=image_ipfs, image_gateway_url=image_gateway,
            metadata_cid=meta_cid, metadata_url=meta_ipfs, metadata_uri=meta_gateway,
            provider="pinata",
        )

    def _upload_via_nft_storage(self, image_path, name, symbol, description, twitter, telegram, website, creator_address) -> IpfsResult:
        nfts = NftStorageUploader(config.NFT_STORAGE_API_KEY)
        image_cid = nfts.upload_file(image_path)
        image_ipfs = f"ipfs://{image_cid}"
        # Build + upload metadata
        from src.metadata import MetadataGenerator
        meta_gen = MetadataGenerator()
        metadata = meta_gen.build_metaplex_metadata(name, symbol, description, image_ipfs, website, twitter, telegram, creator_address)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as tmp:
            json.dump(metadata, tmp)
            meta_cid = nfts.upload_file(tmp.name)
        meta_ipfs = f"ipfs://{meta_cid}"
        return IpfsResult(
            image_cid=image_cid, image_url=image_ipfs, image_gateway_url=f"https://nftstorage.link/ipfs/{image_cid}",
            metadata_cid=meta_cid, metadata_url=meta_ipfs, metadata_uri=f"https://nftstorage.link/ipfs/{meta_cid}",
            provider="nftstorage",
        )
