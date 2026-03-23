# 🚀 TokenLaunchKit

End-to-end Solana token launcher. One command goes from idea → live token on PumpFun with IPFS metadata, AI-generated logo, and a ready-to-deploy landing page.

**Built by LixerDev**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Solana](https://img.shields.io/badge/network-Solana-9945FF)
![PumpFun](https://img.shields.io/badge/platform-PumpFun-ff69b4)

---

## ⚡ Quick Start

```bash
git clone https://github.com/LixerDev/TokenLaunchKit.git
cd TokenLaunchKit
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys

# Full launch in one command
python main.py launch --name "DOGE2" --symbol "DOGE2" \
  --description "The next evolution of doge" \
  --twitter "https://twitter.com/doge2sol" \
  --telegram "https://t.me/doge2sol" \
  --initial-buy 0.1

# Or from a JSON config file
python main.py launch --config examples/my_token.json

# Dry run (generates everything, skips actual launch)
python main.py launch --name "DOGE2" --symbol "D2" --dry-run
```

---

## 🔄 Full Launch Pipeline

```
1. validate        → Check all fields, verify wallet has enough SOL
2. generate image  → DALL-E 3 generates a token logo from description
3. upload IPFS     → Image + metadata JSON uploaded to Pinata / pump.fun IPFS
4. launch PumpFun  → Creates bonding curve + optional initial buy
5. generate page   → Landing page HTML auto-generated with mint address
6. save receipt    → JSON receipt saved with all addresses and links
```

---

## 🛠️ All Commands

```bash
# ── LAUNCH ───────────────────────────────────────────────────────────────────

# Minimal launch (AI fills in description + generates logo)
python main.py launch --name "GigaSOL" --symbol "GSOL"

# Full config via flags
python main.py launch \
  --name "GigaSOL" \
  --symbol "GSOL" \
  --description "The gigachad Solana memecoin" \
  --image ./logo.png \           # Use your own image (skips AI generation)
  --twitter "https://twitter.com/gigasol" \
  --telegram "https://t.me/gigasol" \
  --website "https://gigasol.fun" \
  --initial-buy 0.5 \            # Buy 0.5 SOL worth on launch
  --slippage 10 \
  --priority-fee 0.001

# From config file
python main.py launch --config examples/my_token.json

# Dry run — generates everything but does NOT broadcast
python main.py launch --name "GigaSOL" --symbol "GSOL" --dry-run

# ── INDIVIDUAL STEPS ─────────────────────────────────────────────────────────

# Just generate metadata (name suggestions, description, tags)
python main.py generate --name "GigaSOL" --vibe "bullish memecoin"

# Just generate an AI logo
python main.py image --name "GigaSOL" --style "cartoon"

# Just upload files to IPFS
python main.py upload --image ./logo.png --name "GigaSOL" --symbol "GSOL"

# Just generate the landing page (for an already-launched token)
python main.py page \
  --mint "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA" \
  --name "GigaSOL" \
  --symbol "GSOL" \
  --description "..." \
  --image-url "https://..." \
  --output ./site/index.html

# Validate a config file without launching
python main.py validate --config examples/my_token.json
```

---

## 📁 Config File Format

```json
{
  "name": "GigaSOL",
  "symbol": "GSOL",
  "description": "The gigachad Solana memecoin — no utility, pure vibes.",
  "image": "./logo.png",
  "twitter": "https://twitter.com/gigasol",
  "telegram": "https://t.me/gigasol",
  "website": "https://gigasol.fun",
  "initial_buy_sol": 0.5,
  "slippage": 10,
  "priority_fee_sol": 0.001,
  "image_style": "cartoon",
  "generate_image": true,
  "generate_landing": true
}
```

---

## 📤 IPFS Upload

TokenLaunchKit uploads to **Pinata** by default with fallback to **pump.fun's native IPFS** endpoint.

```bash
# Pinata (recommended — free tier: 1GB)
PINATA_JWT=eyJ...

# pump.fun IPFS (no key needed, uses their endpoint)
USE_PUMPFUN_IPFS=true
```

Metadata JSON format (Metaplex standard):
```json
{
  "name": "GigaSOL",
  "symbol": "GSOL",
  "description": "The gigachad Solana memecoin",
  "image": "ipfs://bafybeig...",
  "external_url": "https://gigasol.fun",
  "attributes": [],
  "properties": {
    "files": [{ "uri": "ipfs://...", "type": "image/png" }],
    "category": "image",
    "creators": [{ "address": "<WALLET>", "share": 100 }]
  }
}
```

---

## 🌐 Landing Page

Auto-generated from `src/landing.py` — a single-file HTML page with:

- Token name, symbol, logo
- Contract address with one-click copy
- "Buy on PumpFun" button
- Live chart embed (Dexscreener iframe)
- Social links (Twitter, Telegram, Website)
- Tokenomics section
- Countdown timer (configurable launch time)
- No external dependencies — works as a static file

---

## 📊 Launch Receipt

After a successful launch, a JSON receipt is saved:

```json
{
  "status": "success",
  "token": {
    "name": "GigaSOL",
    "symbol": "GSOL",
    "mint": "...",
    "decimals": 6,
    "total_supply": 1000000000
  },
  "ipfs": {
    "image_url": "ipfs://...",
    "metadata_url": "ipfs://...",
    "metadata_uri": "https://gateway.pinata.cloud/..."
  },
  "pumpfun": {
    "bonding_curve": "...",
    "transaction": "...",
    "pumpfun_url": "https://pump.fun/...",
    "dexscreener_url": "https://dexscreener.com/solana/..."
  },
  "landing_page": "./output/gigasol/index.html",
  "launched_at": "2025-01-01T12:00:00Z"
}
```

---

## 🏗️ Architecture

```
main.py                 CLI (launch, generate, upload, image, page, validate)
config.py               Config loader (.env + CLI flags + JSON)
src/
  models.py             TokenConfig, LaunchResult, IpfsResult, PumpFunResult
  metadata.py           AI metadata generator (OpenAI GPT-4 for descriptions)
  image.py              AI logo generator (DALL-E 3) + local image processor
  ipfs.py               IPFS uploader (Pinata + pump.fun native)
  pumpfun.py            PumpFun launcher (metadata upload + on-chain tx)
  landing.py            HTML landing page generator (self-contained)
  validator.py          Config validator (fields, wallet balance, image size)
  logger.py             Rich-formatted logging

examples/
  my_token.json         Example config file
  meme_token.json       Memecoin config with AI generation
  defi_token.json       DeFi token config

output/                 Generated files (gitignored)
  <token-name>/
    logo.png            Generated/processed logo
    metadata.json       IPFS metadata
    index.html          Landing page
    receipt.json        Launch receipt
```
