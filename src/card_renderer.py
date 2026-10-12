import base64
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageOps
from src.config import BASE_DIR, TEMP_DIR

logger = logging.getLogger(__name__)

# Color themes matching our 4 daily slots
SLOT_THEMES = {
    "morning": {
        "badge_border": "rgba(56, 189, 248, 0.65)",
        "badge_bg": "rgba(14, 165, 233, 0.22)",
        "badge_color": "#38bdf8",
        "avatar_border": "#38bdf8",
        "avatar_glow": "rgba(56, 189, 248, 0.6)",
        "brand_border": "rgba(56, 189, 248, 0.4)",
        "default_category": "Artificial Intelligence",
        "icon": "🤖"
    },
    "noon": {
        "badge_border": "rgba(52, 211, 153, 0.65)",
        "badge_bg": "rgba(16, 185, 129, 0.22)",
        "badge_color": "#34d399",
        "avatar_border": "#34d399",
        "avatar_glow": "rgba(52, 211, 153, 0.6)",
        "brand_border": "rgba(52, 211, 153, 0.4)",
        "default_category": "Tech & Innovation",
        "icon": "⚡"
    },
    "afternoon": {
        "badge_border": "rgba(251, 191, 36, 0.65)",
        "badge_bg": "rgba(245, 158, 11, 0.22)",
        "badge_color": "#fbbf24",
        "avatar_border": "#fbbf24",
        "avatar_glow": "rgba(251, 191, 36, 0.6)",
        "brand_border": "rgba(251, 191, 36, 0.4)",
        "default_category": "Cybersecurity & Privacy",
        "icon": "🛡️"
    },
    "night": {
        "badge_border": "rgba(192, 132, 252, 0.65)",
        "badge_bg": "rgba(168, 85, 247, 0.22)",
        "badge_color": "#c084fc",
        "avatar_border": "#c084fc",
        "avatar_glow": "rgba(192, 132, 252, 0.6)",
        "brand_border": "rgba(192, 132, 252, 0.4)",
        "default_category": "Science & Deep Space",
        "icon": "🌌"
    }
}

class PhotoCardRenderer:
    """
    Renders editorial-quality Bengali Photo Cards (ফটোকার্ড) matching the style
    of leading tech & science media outlets (e.g., BigyanPriyo, Wired, BBC).
    
    Features:
    - Flawless Bengali OpenType text shaping (HarfBuzz/Chromium engine).
    - 100% Offline Zero-Network font and image embedding (base64).
    - Cinematic gradient dark overlay for maximum text legibility.
    - Two-tone punchy typography (White + Golden Yellow highlight).
    - Category pill badge & page branding.
    - 1080x1080 Instagram/Facebook square resolution.
    - Second-tier Pillow Fail-Safe Engine ensuring branding is never omitted.
    """

    def __init__(self, font_path: Optional[Path] = None, avatar_path: Optional[Path] = None):
        self.font_bengali_path = font_path or (BASE_DIR / "assets" / "fonts" / "HindSiliguri-Bold.ttf")
        self.font_english_path = BASE_DIR / "assets" / "fonts" / "PlusJakartaSans-Bold.ttf"
        self.avatar_path = avatar_path or (BASE_DIR / "assets" / "page_profile_pic.png")
        self._font_b64 = None
        self._english_font_b64 = None
        self._avatar_b64 = None
        self.browser_bin = self._locate_browser()
        if self.browser_bin:
            logger.info(f"📸 Headless browser located for PhotoCard rendering: {self.browser_bin}")
        else:
            logger.warning("⚠️ No headless browser found. PhotoCards will use Pillow fail-safe engine.")

    def _locate_browser(self) -> Optional[str]:
        """Finds Chrome, Chromium, or Edge binary on Windows or Linux."""
        # 1. Check system PATH
        for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge"]:
            found = shutil.which(name)
            if found:
                return found

        # 2. Check standard Windows paths
        win_candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for path in win_candidates:
            if os.path.exists(path):
                return path

        # 3. Check standard Linux / GitHub Actions runner paths
        linux_candidates = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser"
        ]
        for path in linux_candidates:
            if os.path.exists(path):
                return path

        return None

    def _get_bengali_font_b64(self) -> str:
        """Returns base64 encoded Bengali font for self-contained offline embedding."""
        if self._font_b64 is None:
            if self.font_bengali_path.exists():
                with open(self.font_bengali_path, "rb") as f:
                    self._font_b64 = base64.b64encode(f.read()).decode("utf-8")
            else:
                self._font_b64 = ""
        return self._font_b64

    def _get_english_font_b64(self) -> str:
        """Returns base64 encoded English font for self-contained offline embedding."""
        if self._english_font_b64 is None:
            if self.font_english_path.exists():
                with open(self.font_english_path, "rb") as f:
                    self._english_font_b64 = base64.b64encode(f.read()).decode("utf-8")
            else:
                self._english_font_b64 = ""
        return self._english_font_b64

    def _get_avatar_b64(self) -> str:
        """Returns base64 encoded page avatar image for brand embedding."""
        if self._avatar_b64 is None:
            if self.avatar_path.exists():
                with open(self.avatar_path, "rb") as f:
                    self._avatar_b64 = base64.b64encode(f.read()).decode("utf-8")
            else:
                self._avatar_b64 = ""
        return self._avatar_b64

    def render_photo_card(
        self,
        base_image_path: Path,
        headline: str,
        category: str = "",
        highlight_words: str = "",
        slot: str = "morning",
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Composes a high-impact editorial Photo Card from the base image and headline text.
        Guaranteed: Never falls back to unbranded raw image. Uses Pillow fail-safe if browser fails.
        """
        target_path = output_path or base_image_path.with_name(f"{base_image_path.stem}_card.jpg")

        if not base_image_path.exists():
            logger.warning(f"Base image not found at {base_image_path}")
            return base_image_path

        theme = SLOT_THEMES.get(slot, SLOT_THEMES["morning"])
        display_category = category.strip() if category.strip() else theme["default_category"]
        clean_headline = self._clean_card_text(headline)
        formatted_headline = self._apply_highlights(clean_headline, highlight_words)

        # If no headless browser is available, use Pillow fail-safe immediately
        if not self.browser_bin:
            logger.info("Headless browser not detected. Using Pillow Fail-Safe Engine directly.")
            return self._render_pillow_fallback(
                base_image_path=base_image_path,
                headline=clean_headline,
                category=display_category,
                highlight_words=highlight_words,
                slot=slot,
                output_path=target_path
            )

        try:
            # Encode background image
            with open(base_image_path, "rb") as img_file:
                bg_b64 = base64.b64encode(img_file.read()).decode("utf-8")

            bengali_font_b64 = self._get_bengali_font_b64()
            english_font_b64 = self._get_english_font_b64()
            avatar_b64 = self._get_avatar_b64()

            font_face_css = ""
            if bengali_font_b64:
                font_face_css += f"""
                @font-face {{
                    font-family: 'Hind Siliguri';
                    src: url('data:font/truetype;charset=utf-8;base64,{bengali_font_b64}') format('truetype');
                    font-weight: 700;
                    font-style: normal;
                }}
                """
            if english_font_b64:
                font_face_css += f"""
                @font-face {{
                    font-family: 'Plus Jakarta Sans';
                    src: url('data:font/truetype;charset=utf-8;base64,{english_font_b64}') format('truetype');
                    font-weight: 800;
                    font-style: normal;
                }}
                """

            avatar_html = (
                f'<img src="data:image/png;base64,{avatar_b64}" class="avatar-circle">'
                if avatar_b64
                else f'<span class="logo-icon">{theme["icon"]}</span>'
            )

            # 100% Offline HTML Template (ZERO online network requests)
            html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  {font_face_css}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1080px;
    position: relative;
    overflow: hidden;
    background: #080c16;
    font-family: 'Hind Siliguri', 'Plus Jakarta Sans', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }}
  .bg-image {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    object-fit: cover;
    z-index: 1;
  }}
  .gradient-overlay {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(
      180deg, 
      rgba(7, 11, 20, 0.96) 0%, 
      rgba(7, 11, 20, 0.88) 35%, 
      rgba(7, 11, 20, 0.38) 64%, 
      rgba(7, 11, 20, 0.05) 100%
    );
    z-index: 2;
  }}
  .content-container {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    padding: 60px 70px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    z-index: 3;
  }}
  .top-meta {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 35px;
  }}
  .brand-identity {{
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(15, 23, 42, 0.70);
    backdrop-filter: blur(14px);
    padding: 6px 22px 6px 8px;
    border-radius: 999px;
    border: 1.5px solid {theme['brand_border']};
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  }}
  .avatar-circle {{
    width: 60px;
    height: 60px;
    border-radius: 50%;
    object-fit: cover;
    border: 2.5px solid {theme['avatar_border']};
    box-shadow: 0 0 16px {theme['avatar_glow']};
  }}
  .logo-icon {{
    font-size: 32px;
    line-height: 1;
    margin-left: 6px;
  }}
  .brand-name {{
    color: #ffffff;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }}
  .category-badge {{
    background: {theme['badge_bg']};
    border: 1.5px solid {theme['badge_border']};
    color: {theme['badge_color']};
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 20px;
    font-weight: 800;
    padding: 10px 24px;
    border-radius: 999px;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .headline {{
    color: #ffffff;
    font-size: 52px;
    font-weight: 700;
    line-height: 1.35;
    text-shadow: 0 4px 18px rgba(0,0,0,0.85);
    max-width: 940px;
  }}
  .headline .highlight {{
    color: #facc15;
    text-shadow: 0 0 28px rgba(250, 204, 21, 0.45);
    display: inline;
  }}
</style>
</head>
<body>
  <img src="data:image/jpeg;base64,{bg_b64}" class="bg-image">
  <div class="gradient-overlay"></div>
  <div class="content-container">
    <div class="top-meta">
      <div class="brand-identity">
        {avatar_html}
        <span class="brand-name">Be Smart With AI</span>
      </div>
      <div class="category-badge">{display_category}</div>
    </div>
    <div class="headline">
      {formatted_headline}
    </div>
  </div>
</body>
</html>"""

            temp_html = TEMP_DIR / "photocard_render.html"
            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(html_content)

            # Clean stale target file before taking new screenshot
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    pass

            file_url = temp_html.resolve().as_uri()
            cmd = [
                self.browser_bin,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--run-all-compositor-stages-before-draw",
                f"--screenshot={str(target_path.resolve())}",
                "--window-size=1080,1080",
                "--hide-scrollbars",
                file_url
            ]

            logger.info("Executing headless browser to render editorial PhotoCard (100% offline)...")
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0 and target_path.exists() and target_path.stat().st_size > 5000:
                logger.info(f"🎉 PhotoCard successfully rendered at {target_path} ({target_path.stat().st_size:,} bytes)")
                return target_path
            else:
                logger.warning(f"Browser rendering returned non-zero code ({res.returncode}): {res.stderr}. Switching to Pillow fail-safe engine...")
                return self._render_pillow_fallback(
                    base_image_path=base_image_path,
                    headline=clean_headline,
                    category=display_category,
                    highlight_words=highlight_words,
                    slot=slot,
                    output_path=target_path
                )

        except Exception as e:
            logger.error(f"Error rendering PhotoCard via browser: {e}. Switching to Pillow fail-safe engine...")
            return self._render_pillow_fallback(
                base_image_path=base_image_path,
                headline=clean_headline,
                category=display_category,
                highlight_words=highlight_words,
                slot=slot,
                output_path=target_path
            )

    def _render_pillow_fallback(
        self,
        base_image_path: Path,
        headline: str,
        category: str,
        highlight_words: str,
        slot: str,
        output_path: Path
    ) -> Path:
        """
        Guaranteed fail-safe Pillow engine that composites the editorial PhotoCard
        even if headless Chrome is unavailable or times out.
        """
        try:
            logger.info("🎨 Activating Pillow Fail-Safe Engine for PhotoCard composition...")
            img = Image.open(base_image_path).convert("RGBA")
            img = ImageOps.fit(img, (1080, 1080), method=Image.Resampling.LANCZOS)

            # 1. Dark gradient overlay
            overlay = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)
            for y in range(480):
                alpha = int(245 * (1.0 - (y / 480) ** 1.3))
                draw_overlay.line([(0, y), (1080, y)], fill=(7, 11, 20, alpha))
            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)

            theme = SLOT_THEMES.get(slot, SLOT_THEMES["morning"])
            display_category = category.strip() if category.strip() else theme["default_category"]

            theme_color_map = {
                "morning": (56, 189, 248),
                "noon": (52, 211, 153),
                "afternoon": (251, 191, 36),
                "night": (192, 132, 252)
            }
            accent_rgb = theme_color_map.get(slot, (56, 189, 248))

            # 2. Brand Identity Pill (Top Left)
            draw.rounded_rectangle([(60, 50), (410, 120)], radius=35, fill=(15, 23, 42, 200), outline=accent_rgb, width=2)
            
            # Avatar circle
            if self.avatar_path.exists():
                try:
                    avatar = Image.open(self.avatar_path).convert("RGBA").resize((56, 56), Image.Resampling.LANCZOS)
                    mask = Image.new("L", (56, 56), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([(0, 0), (55, 55)], fill=255)
                    img.paste(avatar, (66, 57), mask)
                    draw.ellipse([(65, 56), (123, 114)], outline=accent_rgb, width=2)
                except Exception as av_err:
                    logger.debug(f"Pillow avatar paste error: {av_err}")

            # Brand text
            eng_font = ImageFont.truetype(str(self.font_english_path), 22) if self.font_english_path.exists() else None
            draw.text((135, 72), "Be Smart With AI", fill=(255, 255, 255), font=eng_font)

            # 3. Category Badge (Top Right)
            cat_text = display_category.upper()
            cat_w = len(cat_text) * 12 + 40
            cat_x1 = max(680, 1020 - cat_w)
            draw.rounded_rectangle([(cat_x1, 58), (1020, 112)], radius=27, fill=(15, 23, 42, 200), outline=accent_rgb, width=2)
            draw.text((cat_x1 + 20, 72), cat_text, fill=accent_rgb, font=eng_font)

            # 4. Bengali Headline Text
            bengali_font = ImageFont.truetype(str(self.font_bengali_path), 46) if self.font_bengali_path.exists() else None
            clean_head = self._clean_card_text(headline)
            
            # Word-wrap to max 2 lines
            words = clean_head.split()
            mid = len(words) // 2 + 1 if len(words) > 6 else len(words)
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:]) if len(words) > mid else ""

            # Draw lines with drop shadow for maximum clarity
            y_offset = 160
            for line in [line1, line2]:
                if not line:
                    continue
                # Shadow
                draw.text((72, y_offset + 3), line, fill=(0, 0, 0), font=bengali_font)
                draw.text((70, y_offset), line, fill=(255, 255, 255), font=bengali_font)
                y_offset += 65

            # Save JPEG
            final_img = img.convert("RGB")
            final_img.save(output_path, "JPEG", quality=95)
            logger.info(f"🛡️ Pillow fail-safe PhotoCard saved successfully to {output_path} ({output_path.stat().st_size:,} bytes)")
            return output_path

        except Exception as p_err:
            logger.error(f"Pillow fail-safe renderer failed: {p_err}. Falling back to base image.")
            return base_image_path

    def _clean_card_text(self, text: str) -> str:
        """Removes outer quotation marks and leading emojis for a clean editorial headline."""
        cleaned = text.strip()
        cleaned = re.sub(r"^[\U00010000-\U0010ffff\u2600-\u27bf\s]+", "", cleaned)
        cleaned = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\s]+$", "", cleaned)
        return cleaned.strip()

    def _apply_highlights(self, headline: str, highlight_words: str) -> str:
        """Applies yellow highlight formatting to key words in the headline."""
        if highlight_words and highlight_words.strip():
            clean_hw = highlight_words.strip().strip("'\"")
            if clean_hw in headline:
                return headline.replace(clean_hw, f'<span class="highlight">{clean_hw}</span>', 1)

        quote_match = re.search(r"['\"](.*?)['\"]", headline)
        if quote_match:
            quoted_text = quote_match.group(0)
            inner_text = quote_match.group(1)
            return headline.replace(quoted_text, f'<span class="highlight">{inner_text}</span>', 1)

        words = headline.split()
        if len(words) >= 5:
            prefix = " ".join(words[:-3])
            highlight_part = " ".join(words[-3:])
            return f'{prefix} <span class="highlight">{highlight_part}</span>'

        return headline
