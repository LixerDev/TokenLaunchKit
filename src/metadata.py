"""
Metadata Generator — AI-assisted token metadata generation.

Uses GPT-4o to generate:
- Token descriptions with the right memecoin energy
- Name suggestions from a theme/vibe
- Symbol ideas
- Tags and attributes

Built by LixerDev / TokenLaunchKit
"""

import json
from src.logger import get_logger
from config import config

logger = get_logger(__name__)


class MetadataGenerator:
    """Generates token metadata using OpenAI GPT-4o."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client:
            if not config.has_openai():
                raise ValueError("OPENAI_API_KEY not set. Add it to your .env file.")
            from openai import OpenAI
            self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        return self._client

    def generate_description(self, name: str, symbol: str, vibe: str = "") -> str:
        """
        Generate a compelling token description using GPT-4o.

        Parameters:
        - name: Token name (e.g. "GigaSOL")
        - symbol: Token symbol (e.g. "GSOL")
        - vibe: Optional theme hint (e.g. "bullish memecoin", "AI utility token")

        Returns:
        - str: 2–4 sentence token description
        """
        vibe_hint = f" The vibe: {vibe}." if vibe else ""
        prompt = (
            f"Write a short, punchy Solana token description for a token called '{name}' (${symbol}).{vibe_hint}\n\n"
            "Requirements:\n"
            "- 2–3 sentences maximum\n"
            "- Crypto/memecoin energy — confident, fun, no BS\n"
            "- Mention Solana\n"
            "- Do NOT use clichés like 'to the moon' or 'diamond hands'\n"
            "- Do NOT mention price targets or financial advice\n"
            "- Return only the description, no quotes or extra text"
        )
        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.9,
            )
            description = resp.choices[0].message.content.strip()
            logger.info(f"Generated description for {name}")
            return description
        except Exception as e:
            logger.error(f"GPT description failed: {e}")
            return f"{name} — the next Solana memecoin. Built different. On-chain forever. ${symbol}"

    def suggest_names(self, theme: str, count: int = 5) -> list[dict]:
        """
        Generate token name + symbol suggestions for a given theme.

        Returns list of {"name": ..., "symbol": ..., "tagline": ...}
        """
        prompt = (
            f"Generate {count} Solana memecoin name + ticker suggestions for this theme: {theme!r}\n\n"
            "Format each as JSON with keys: name, symbol (max 8 chars, uppercase), tagline (max 10 words)\n"
            "Return a JSON array only, no other text.\n"
            "Make them catchy, crypto-native, and memorable."
        )
        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=1.0,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content.strip()
            data = json.loads(raw)
            # Handle both {"names": [...]} and direct array
            if isinstance(data, list):
                return data
            return data.get("names", data.get("suggestions", []))[:count]
        except Exception as e:
            logger.error(f"Name suggestions failed: {e}")
            return [{"name": "GigaSOL", "symbol": "GSOL", "tagline": "Built different on Solana"}]

    def generate_image_prompt(self, name: str, description: str, style: str = "vibrant") -> str:
        """
        Generate a DALL-E prompt for a token logo.

        Parameters:
        - name: Token name
        - description: Token description
        - style: "vibrant" | "cartoon" | "pixel" | "realistic" | "minimal" | "retro"

        Returns:
        - str: DALL-E 3 prompt
        """
        style_prompts = {
            "vibrant": "vibrant colors, glossy, bold, crypto logo style",
            "cartoon": "cartoon style, cute, bold outlines, fun, colorful",
            "pixel": "pixel art, 8-bit, retro game style, bright colors",
            "realistic": "photorealistic, detailed, high quality render, dramatic lighting",
            "minimal": "minimalist, clean, flat design, monochrome with accent color",
            "retro": "retro 80s style, synthwave colors, neon, chrome text",
        }

        style_desc = style_prompts.get(style, style_prompts["vibrant"])

        prompt_gen_prompt = (
            f"Write a DALL-E 3 image prompt to generate a crypto token logo for '{name}'.\n"
            f"Token description: {description[:200]}\n"
            f"Style requirement: {style_desc}\n\n"
            "Requirements:\n"
            "- Square format logo suitable for a crypto token\n"
            "- Clear, recognizable symbol or mascot\n"
            "- No text in the image (logos never have text)\n"
            "- Professional quality\n"
            "Return only the DALL-E prompt, nothing else."
        )

        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt_gen_prompt}],
                max_tokens=200,
                temperature=0.8,
            )
            prompt = resp.choices[0].message.content.strip()
            logger.debug(f"Image prompt: {prompt[:80]}...")
            return prompt
        except Exception as e:
            logger.warning(f"Image prompt generation failed: {e}, using default")
            return (
                f"A crypto token logo for '{name}', {style_desc}, "
                "square format, no text, high quality, professional"
            )

    def build_metaplex_metadata(
        self,
        name: str,
        symbol: str,
        description: str,
        image_url: str,
        website: str = "",
        twitter: str = "",
        telegram: str = "",
        creator_address: str = "",
    ) -> dict:
        """
        Build a Metaplex-compatible metadata JSON object.

        This is the standard format used by Solana NFT/token protocols.
        """
        metadata = {
            "name": name,
            "symbol": symbol,
            "description": description,
            "image": image_url,
            "external_url": website or "",
            "attributes": [],
            "properties": {
                "files": [
                    {
                        "uri": image_url,
                        "type": "image/png",
                    }
                ],
                "category": "image",
            },
        }

        if creator_address:
            metadata["properties"]["creators"] = [
                {"address": creator_address, "share": 100}
            ]

        links = {}
        if twitter:
            links["twitter"] = twitter
        if telegram:
            links["telegram"] = telegram
        if website:
            links["website"] = website

        if links:
            metadata["extensions"] = links

        return metadata
