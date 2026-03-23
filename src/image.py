"""
Image Generator — AI logo generation + image processing.

Supports:
- DALL-E 3 via OpenAI API (primary)
- Local image file processing (resize, optimize for IPFS)

Built by LixerDev / TokenLaunchKit
"""

import requests
import base64
from pathlib import Path
from PIL import Image
import io
from src.logger import get_logger
from config import config

logger = get_logger(__name__)

TARGET_SIZE = (512, 512)
MAX_FILE_SIZE_KB = 500
SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


class ImageGenerator:
    """Generate and process token logo images."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            if not config.has_openai():
                raise ValueError("OPENAI_API_KEY not set — needed for AI image generation.")
            from openai import OpenAI
            self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        return self._client

    def generate_ai_logo(self, prompt: str, output_path: str) -> str:
        """
        Generate a token logo using DALL-E 3.

        Parameters:
        - prompt: Detailed image description
        - output_path: Where to save the PNG file

        Returns:
        - str: Path to saved image file

        Raises:
        - ValueError: If OpenAI API key not configured
        - RuntimeError: If generation fails
        """
        logger.info("Generating AI logo with DALL-E 3...")
        logger.debug(f"Prompt: {prompt[:100]}...")

        try:
            client = self._get_client()
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="hd",
                n=1,
                response_format="b64_json",
            )

            image_data = base64.b64decode(response.data[0].b64_json)
            img = Image.open(io.BytesIO(image_data))

            # Process and save
            return self._process_and_save(img, output_path)

        except Exception as e:
            raise RuntimeError(f"DALL-E 3 generation failed: {e}") from e

    def process_local_image(self, input_path: str, output_path: str) -> str:
        """
        Process a local image file: resize, optimize, and save as PNG.

        Accepts: PNG, JPG, JPEG, GIF, WebP
        Output: 512x512 PNG optimized for IPFS

        Parameters:
        - input_path: Source image path
        - output_path: Destination PNG path

        Returns:
        - str: Path to processed image
        """
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {input_path}")
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {path.suffix}. Use: {', '.join(SUPPORTED_FORMATS)}")

        logger.info(f"Processing local image: {input_path}")

        img = Image.open(input_path)
        return self._process_and_save(img, output_path)

    def download_image(self, url: str, output_path: str) -> str:
        """Download an image from a URL and process it."""
        logger.info(f"Downloading image from: {url[:60]}...")

        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        img = Image.open(io.BytesIO(resp.content))
        return self._process_and_save(img, output_path)

    def _process_and_save(self, img: Image.Image, output_path: str) -> str:
        """
        Resize to 512x512, convert to RGBA PNG, optimize file size.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Convert to RGBA
        if img.mode not in ("RGBA", "RGB"):
            img = img.convert("RGBA")

        # Resize to square
        img = self._smart_resize(img, TARGET_SIZE)

        # Save as PNG
        output = Path(output_path).with_suffix(".png")

        # Try to keep under MAX_FILE_SIZE_KB
        for quality in [95, 85, 75, 60]:
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            size_kb = buf.tell() / 1024
            if size_kb <= MAX_FILE_SIZE_KB:
                break

        img.save(str(output), format="PNG", optimize=True)
        final_size = Path(str(output)).stat().st_size / 1024
        logger.info(f"Image saved: {output} ({final_size:.1f} KB)")
        return str(output)

    def _smart_resize(self, img: Image.Image, target: tuple[int, int]) -> Image.Image:
        """Resize with aspect ratio preserved + center-crop to square."""
        target_w, target_h = target
        orig_w, orig_h = img.size

        # Scale to fit the larger dimension
        scale = max(target_w / orig_w, target_h / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Center crop to target size
        left = (new_w - target_w) // 2
        top  = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))

        return img

    def get_image_info(self, path: str) -> dict:
        """Return basic info about an image file."""
        img = Image.open(path)
        size = Path(path).stat().st_size
        return {
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "format": img.format,
            "size_kb": round(size / 1024, 1),
        }
