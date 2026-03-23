"""
Landing Page Generator — Creates a beautiful token landing page.

Output: a single self-contained HTML file with no external dependencies.
Built by LixerDev / TokenLaunchKit
"""

from pathlib import Path
from src.logger import get_logger

logger = get_logger(__name__)


class LandingPageGenerator:
    """
    Generates a professional token landing page from token metadata.

    The output is a single HTML file — no build step, no npm, no framework.
    Everything is inlined: CSS, JS, chart embed, copy-to-clipboard.

    Features:
    - Token name, symbol, logo
    - Contract address (click-to-copy)
    - Buy on PumpFun button
    - Live chart (Dexscreener embed)
    - Social links (Twitter, Telegram, Website)
    - Animated particle background
    - Mobile responsive
    """

    def generate(
        self,
        output_path: str,
        name: str,
        symbol: str,
        description: str,
        mint: str,
        image_url: str = "",
        twitter: str = "",
        telegram: str = "",
        website: str = "",
        pumpfun_url: str = "",
        dexscreener_url: str = "",
        total_supply: str = "1,000,000,000",
        decimals: int = 6,
    ) -> str:
        """
        Generate the landing page HTML.

        Parameters:
        - output_path: Where to save the HTML file
        - name: Token name
        - symbol: Token symbol (without $)
        - description: Token description
        - mint: Solana mint address
        - image_url: Token logo URL (IPFS or HTTP)
        - twitter/telegram/website: Social links
        - pumpfun_url: Direct PumpFun link
        - dexscreener_url: Dexscreener chart link

        Returns:
        - str: Path to generated HTML file
        """
        pumpfun_url = pumpfun_url or f"https://pump.fun/{mint}"
        dexscreener_url = dexscreener_url or f"https://dexscreener.com/solana/{mint}"
        short_mint = f"{mint[:4]}...{mint[-4:]}" if len(mint) > 12 else mint

        html = self._render_template(
            name=name, symbol=symbol, description=description,
            mint=mint, short_mint=short_mint, image_url=image_url,
            twitter=twitter, telegram=telegram, website=website,
            pumpfun_url=pumpfun_url, dexscreener_url=dexscreener_url,
            total_supply=total_supply, decimals=decimals,
        )

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Landing page generated: {output_path}")
        return output_path

    def _render_template(self, **ctx) -> str:
        name         = ctx["name"]
        symbol       = ctx["symbol"]
        description  = ctx["description"]
        mint         = ctx["mint"]
        short_mint   = ctx["short_mint"]
        image_url    = ctx["image_url"]
        twitter      = ctx["twitter"]
        telegram     = ctx["telegram"]
        website      = ctx["website"]
        pumpfun_url  = ctx["pumpfun_url"]
        dex_url      = ctx["dexscreener_url"]
        total_supply = ctx["total_supply"]

        # Social links HTML
        social_links = ""
        if twitter:
            social_links += f'<a href="{twitter}" target="_blank" class="social-btn twitter">🐦 Twitter</a>'
        if telegram:
            social_links += f'<a href="{telegram}" target="_blank" class="social-btn telegram">✈️ Telegram</a>'
        if website and website != pumpfun_url:
            social_links += f'<a href="{website}" target="_blank" class="social-btn website">🌐 Website</a>'

        # Logo tag
        logo_html = (
            f'<img src="{image_url}" alt="{name} logo" class="token-logo" onerror="this.style.display=\'none\'">'
            if image_url else
            f'<div class="token-logo-placeholder">${symbol[0]}</div>'
        )

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{description[:160]}">
  <meta property="og:title" content="${symbol} — {name}">
  <meta property="og:description" content="{description[:200]}">
  {f'<meta property="og:image" content="{image_url}">' if image_url else ""}
  <meta name="twitter:card" content="summary_large_image">
  <title>${symbol} — {name}</title>
  <style>
    :root {{
      --bg: #0a0a0f;
      --surface: #12121c;
      --surface2: #1a1a2e;
      --border: #2a2a4a;
      --text: #e8e8f0;
      --dim: #888899;
      --purple: #9945FF;
      --green: #14F195;
      --pink: #ff69b4;
      --glow: rgba(153,69,255,0.3);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: -apple-system, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      overflow-x: hidden;
    }}
    #particles {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }}
    .content {{ position: relative; z-index: 1; }}

    /* ── Hero ── */
    .hero {{
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 40px 20px;
    }}
    .token-logo {{
      width: 140px;
      height: 140px;
      border-radius: 50%;
      border: 3px solid var(--purple);
      box-shadow: 0 0 40px var(--glow), 0 0 80px var(--glow);
      margin-bottom: 24px;
      object-fit: cover;
      animation: float 4s ease-in-out infinite;
    }}
    .token-logo-placeholder {{
      width: 140px; height: 140px; border-radius: 50%;
      background: linear-gradient(135deg, var(--purple), var(--green));
      display: flex; align-items: center; justify-content: center;
      font-size: 56px; font-weight: 800; margin-bottom: 24px;
      box-shadow: 0 0 40px var(--glow);
      animation: float 4s ease-in-out infinite;
    }}
    @keyframes float {{
      0%, 100% {{ transform: translateY(0); }}
      50% {{ transform: translateY(-10px); }}
    }}
    .token-symbol {{
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.2em;
      color: var(--green);
      text-transform: uppercase;
      margin-bottom: 8px;
    }}
    .token-name {{
      font-size: clamp(2.5rem, 8vw, 5rem);
      font-weight: 900;
      background: linear-gradient(135deg, #fff 30%, var(--purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      line-height: 1;
      margin-bottom: 20px;
    }}
    .token-desc {{
      font-size: 1.15rem;
      color: var(--dim);
      max-width: 560px;
      line-height: 1.7;
      margin-bottom: 36px;
    }}

    /* ── Buy Button ── */
    .buy-btn {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      background: linear-gradient(135deg, var(--purple), #7c3aed);
      color: white;
      text-decoration: none;
      padding: 18px 48px;
      border-radius: 50px;
      font-size: 1.1rem;
      font-weight: 800;
      letter-spacing: 0.05em;
      transition: all 0.2s;
      box-shadow: 0 4px 30px var(--glow);
      margin-bottom: 20px;
    }}
    .buy-btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 40px var(--glow); }}

    /* ── Social Buttons ── */
    .social-row {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 40px; }}
    .social-btn {{
      padding: 10px 22px;
      border-radius: 50px;
      font-size: 0.9rem;
      font-weight: 600;
      text-decoration: none;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      transition: all 0.15s;
    }}
    .social-btn:hover {{ border-color: var(--purple); background: var(--surface2); }}

    /* ── Contract Address ── */
    .contract-section {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px 28px;
      max-width: 600px;
      width: 90%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      cursor: pointer;
      transition: border-color 0.15s;
    }}
    .contract-section:hover {{ border-color: var(--purple); }}
    .contract-label {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--dim); letter-spacing: 0.1em; }}
    .contract-addr {{ font-family: monospace; font-size: 0.88rem; color: var(--green); word-break: break-all; }}
    .copy-btn {{
      background: var(--surface2); border: 1px solid var(--border);
      color: var(--dim); padding: 8px 14px; border-radius: 8px;
      cursor: pointer; font-size: 0.8rem; white-space: nowrap;
      transition: all 0.15s; flex-shrink: 0;
    }}
    .copy-btn:hover {{ color: var(--green); border-color: var(--green); }}
    .copy-btn.copied {{ color: var(--green); border-color: var(--green); }}

    /* ── Stats ── */
    .stats-section {{
      padding: 60px 20px;
      max-width: 800px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 20px;
    }}
    .stat-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 28px 20px;
      text-align: center;
    }}
    .stat-value {{ font-size: 1.6rem; font-weight: 800; color: var(--green); }}
    .stat-label {{ font-size: 0.8rem; color: var(--dim); margin-top: 6px; text-transform: uppercase; letter-spacing: 0.08em; }}

    /* ── Chart ── */
    .chart-section {{
      padding: 40px 20px;
      max-width: 900px;
      margin: 0 auto;
    }}
    .chart-section h2 {{ font-size: 1.3rem; font-weight: 700; margin-bottom: 20px; text-align: center; }}
    .chart-embed {{
      width: 100%;
      height: 500px;
      border-radius: 16px;
      border: 1px solid var(--border);
      overflow: hidden;
    }}
    .chart-embed iframe {{ width: 100%; height: 100%; border: none; }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 40px 20px;
      color: var(--dim);
      font-size: 0.82rem;
      border-top: 1px solid var(--border);
    }}
    footer a {{ color: var(--purple); text-decoration: none; }}

    @media (max-width: 600px) {{
      .contract-section {{ flex-direction: column; text-align: center; }}
      .buy-btn {{ padding: 16px 32px; }}
    }}
  </style>
</head>
<body>

<canvas id="particles"></canvas>

<div class="content">

  <!-- ── Hero ── -->
  <section class="hero">
    {logo_html}
    <div class="token-symbol">${symbol}</div>
    <h1 class="token-name">{name}</h1>
    <p class="token-desc">{description}</p>

    <a href="{pumpfun_url}" target="_blank" class="buy-btn">
      🚀 Buy ${symbol} on PumpFun
    </a>

    <div class="social-row">
      {social_links}
      <a href="{dex_url}" target="_blank" class="social-btn">📊 Chart</a>
    </div>

    <!-- Contract Address -->
    <div class="contract-section" onclick="copyCA()">
      <div>
        <div class="contract-label">Contract Address</div>
        <div class="contract-addr" id="ca-text">{mint}</div>
      </div>
      <button class="copy-btn" id="copy-btn">📋 Copy</button>
    </div>
  </section>

  <!-- ── Stats ── -->
  <div class="stats-section">
    <div class="stat-card">
      <div class="stat-value">{total_supply}</div>
      <div class="stat-label">Total Supply</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">0%</div>
      <div class="stat-label">Tax</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">🔒</div>
      <div class="stat-label">LP Locked</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">✅</div>
      <div class="stat-label">Mint Revoked</div>
    </div>
  </div>

  <!-- ── Chart ── -->
  <section class="chart-section">
    <h2>📊 Live Chart</h2>
    <div class="chart-embed">
      <iframe
        src="https://dexscreener.com/solana/{mint}?embed=1&theme=dark&trades=0&info=0"
        allowfullscreen
      ></iframe>
    </div>
  </section>

  <footer>
    <p>${symbol} — {name} | Built on Solana 🟣</p>
    <p style="margin-top:8px">
      <a href="{pumpfun_url}" target="_blank">PumpFun</a> &nbsp;·&nbsp;
      <a href="{dex_url}" target="_blank">Dexscreener</a>
      {f' &nbsp;·&nbsp; <a href="{twitter}" target="_blank">Twitter</a>' if twitter else ""}
      {f' &nbsp;·&nbsp; <a href="{telegram}" target="_blank">Telegram</a>' if telegram else ""}
    </p>
    <p style="margin-top:16px; color:#555; font-size:0.72rem">
      Generated by TokenLaunchKit — LixerDev
    </p>
  </footer>
</div>

<script>
  // ── Copy contract address ──────────────────────────────────────────────
  function copyCA() {{
    const addr = "{mint}";
    navigator.clipboard.writeText(addr).then(() => {{
      const btn = document.getElementById("copy-btn");
      btn.textContent = "✅ Copied!";
      btn.classList.add("copied");
      setTimeout(() => {{
        btn.textContent = "📋 Copy";
        btn.classList.remove("copied");
      }}, 2000);
    }});
  }}

  // ── Particle background ────────────────────────────────────────────────
  const canvas = document.getElementById("particles");
  const ctx2 = canvas.getContext("2d");
  let particles = [];

  function resize() {{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }}
  resize();
  window.addEventListener("resize", resize);

  for (let i = 0; i < 60; i++) {{
    particles.push({{
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 2 + 0.5,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      alpha: Math.random() * 0.5 + 0.1,
    }});
  }}

  function drawParticles() {{
    ctx2.clearRect(0, 0, canvas.width, canvas.height);
    for (const p of particles) {{
      ctx2.beginPath();
      ctx2.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx2.fillStyle = `rgba(153,69,255,${{p.alpha}})`;
      ctx2.fill();
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width)  p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    }}
    requestAnimationFrame(drawParticles);
  }}
  drawParticles();
</script>

</body>
</html>'''
