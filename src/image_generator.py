import os
import time
import logging
import random
import re
import urllib.parse
from pathlib import Path
from typing import Optional, List, Set
import requests
from PIL import Image, ImageDraw, ImageOps, ImageFile
from src.config import BASE_DIR, TEMP_DIR

# Allow loading truncated images to prevent crash on slow or interrupted network streams
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Intelligent Visual Engine that delivers captivating, hyper-realistic, 
    content-matching images for social media posts.
    
    Generation Pipeline:
    - Primary: 100% Photorealistic FLUX AI Generation with context-rich visual prompts.
    - Rate Limit: Intelligent 45s cooldown handling for HTTP 402/429 instead of instant burn.
    - Safety & Quality: Strictly NO female depictions (male professionals / workers / tactile setups only),
      zero abstract glowing orbs/voids, clean watermark removal.
    - Fallback: Sleek modern dark editorial backdrop with zero font text or tofu boxes,
      designed as a pristine canvas for PhotoCardRenderer.
    """
    def __init__(self, output_dir: Path = TEMP_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        # Optional Pollen API key from enter.pollinations.ai for unlimited unthrottled FLUX access
        pollen_key = os.getenv("POLLINATIONS_API_KEY", "").strip() or os.getenv("POLLEN_API_KEY", "").strip()
        if pollen_key:
            self.headers["Authorization"] = f"Bearer {pollen_key}"
            logger.info("🔑 Pollen API key detected: Unlimited high-priority FLUX generation enabled.")
        self.last_image_source: str = ""

    def generate_image(
        self,
        prompt: str,
        title: str = "",
        hero_keywords: Optional[List[str]] = None,
        slot: str = "noon",
        used_image_sources: Optional[Set[str]] = None
    ) -> Optional[Path]:
        """
        Generates or formats an authentic, highly captivating, 1080x1080 image 
        directly matching the post's core subject without repeating past images.
        """
        image_path = self.output_dir / "latest_post_image.jpg"
        self.last_image_source = ""

        # =========================================================================
        # STRATEGY 1: Primary AI Visual Engine (FLUX Photorealism)
        # =========================================================================
        logger.info(f"🎨 [{slot.title()} Slot] Generating custom FLUX AI visual for maximum photorealism and quality...")
        ai_source = self._generate_ai_image(prompt, image_path)
        if ai_source:
            logger.info(f"✅ [{slot.title()} AI] High-quality AI image successfully generated.")
            self.last_image_source = ai_source
            return image_path

        # =========================================================================
        # STRATEGY 2: Editorial Graphic Backdrop Fallback (Zero-Error Local Canvas)
        # =========================================================================
        logger.info("🏷️ [Tier 2 Fallback] Creating branded editorial backdrop canvas...")
        try:
            self.last_image_source = f"editorial_poster_{slot}"
            return self._create_editorial_poster(image_path, title, slot)
        except Exception as e:
            logger.error(f"Failed to create editorial fallback: {e}")
            return None

    def _generate_ai_image(self, prompt: str, output_path: Path) -> Optional[str]:
        """
        Calls Pollinations FLUX AI engine with clean storytelling prompt,
        strict negative constraints, and intelligent 45s cooldown handling for HTTP 402/429.
        """
        clean_prompt = " ".join(prompt.strip().split())

        # 1. First cleanly remove all negation clauses (e.g. 'strictly no female', 'no cartoon', 'without text')
        # to prevent inversion bugs (e.g. 'no female' -> 'no male professional') and stray tokens
        clean_prompt = re.sub(
            r"(?:strictly\s+)?(?:no|never|without)\s+[^,;.]+",
            "",
            clean_prompt,
            flags=re.IGNORECASE
        )

        # 2. Programmatically convert any remaining affirmative female references to male/neutral
        female_words = [
            (r"\bfemale\b", "male professional"),
            (r"\bwoman\b", "man"),
            (r"\bwomen\b", "men"),
            (r"\bgirl\b", "young man"),
            (r"\bgirls\b", "men"),
            (r"\blady\b", "gentleman"),
            (r"\bladies\b", "gentlemen"),
            (r"\bfeminine\b", "masculine"),
        ]
        for pattern, replacement in female_words:
            clean_prompt = re.sub(pattern, replacement, clean_prompt, flags=re.IGNORECASE)

        # 3. Clean up commas and whitespace
        clean_prompt = re.sub(r"\s*,\s*", ", ", clean_prompt)
        clean_prompt = re.sub(r"\s+", " ", clean_prompt).strip(" ,.-")

        # 4. Enhance positive aesthetic for photorealism & authentic textures in well-lit environments
        if not any(token in clean_prompt.lower() for token in ["photorealistic", "photograph", "editorial"]):
            clean_prompt += ", 8k photorealistic editorial documentary photograph, natural daylight, bright modern environment, authentic tactile textures, 35mm lens, sharp focus"

        encoded = urllib.parse.quote(clean_prompt[:800])
        seed = random.randint(100000, 9999999)
        negative_prompt = urllib.parse.quote(
            "female, woman, girl, lady, women, feminine, "
            "cartoon, 3d render, anime, cgi, illustration, drawing, painting, sketch, "
            "abstract orb, glowing sphere, dark empty void, plain blob, floating balls, lens flare in empty space, "
            "dark dim room, turned off screen, blank black monitor, deformed, distorted, bad anatomy, bad hands, blurry, low quality, "
            "text, watermark, signature, logo"
        )

        models = ["flux", "flux-realism", "sana", "turbo"]
        cooldown_handled = False

        for model in models:
            logger.info(f"🎨 Generating visual with AI engine ({model})...")
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1080&model={model}&nologo=true&seed={seed}&negative={negative_prompt}"
            try:
                r = requests.get(url, headers=self.headers, timeout=40)
                if r.status_code == 200 and len(r.content) > 8000:
                    success = self._process_image_bytes(r.content, output_path, is_ai_generated=True)
                    if success:
                        logger.info(f"✨ AI visual generated successfully ({model}, {len(r.content)//1024} KB).")
                        return f"ai_pollinations_{model}_{seed}"
                elif r.status_code in [402, 429, 503]:
                    # Extract wait time from error message or header
                    # e.g. "Free limit reached: 1 image every 45 seconds per IP. Retry after 39s"
                    # or 503: "The Classic API is at its limit right now. Retry after 10s"
                    retry_match = re.search(r"Retry after (\d+)\s*s", r.text, re.IGNORECASE)
                    if retry_match:
                        cooldown = int(retry_match.group(1)) + 1
                    else:
                        retry_after = r.headers.get("Retry-After")
                        default_wait = 12 if r.status_code == 503 else 45
                        cooldown = int(retry_after) if (retry_after and retry_after.isdigit()) else default_wait

                    cooldown = max(5, min(cooldown, 50))

                    if not cooldown_handled:
                        reason = "overload" if r.status_code == 503 else "free limit"
                        logger.warning(
                            f"Pollinations engine '{model}' hit HTTP {r.status_code} ({reason}). "
                            f"Waiting {cooldown}s cooldown before retrying..."
                        )
                        time.sleep(cooldown)
                        cooldown_handled = True

                        # Retry the current model once after cooldown
                        try:
                            logger.info(f"Retrying AI engine ({model}) post-cooldown...")
                            r_retry = requests.get(url, headers=self.headers, timeout=45)
                            if r_retry.status_code == 200 and len(r_retry.content) > 8000:
                                if self._process_image_bytes(r_retry.content, output_path, is_ai_generated=True):
                                    logger.info(f"✨ AI visual generated successfully after cooldown ({model}, {len(r_retry.content)//1024} KB).")
                                    return f"ai_pollinations_{model}_{seed}"
                            else:
                                logger.warning(f"Pollinations retry for '{model}' returned HTTP {r_retry.status_code}. Trying next engine...")
                        except Exception as retry_err:
                            logger.warning(f"Pollinations retry after cooldown failed: {retry_err}. Trying next engine...")
                    else:
                        logger.warning(f"Pollinations engine '{model}' hit HTTP {r.status_code}. Trying next engine...")
                        time.sleep(3)
                else:
                    logger.warning(f"Pollinations engine '{model}' returned HTTP {r.status_code}. Trying next model...")
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"Pollinations {model} network error/timeout: {e}")

        return None

    def _process_image_bytes(self, data: bytes, output_path: Path, is_ai_generated: bool = False) -> bool:
        """Loads image data, crops watermark if AI generated, fits into centered 1080x1080, and saves as JPEG."""
        import io
        try:
            img = Image.open(io.BytesIO(data))
            if is_ai_generated:
                w, h = img.size
                # Crop bottom watermark cleanly (at least 55px or 6.5% of height)
                crop_px = max(55, int(h * 0.065))
                if h > 100:
                    img = img.crop((0, 0, w, h - crop_px))
            fitted = ImageOps.fit(img, (1080, 1080), method=Image.Resampling.LANCZOS)
            fitted.convert("RGB").save(output_path, "JPEG", quality=95)
            return True
        except Exception as e:
            logger.error(f"Image formatting error: {e}")
            return False

    def _create_editorial_poster(self, output_path: Path, title: str = "", slot: str = "noon") -> Path:
        """
        Creates an ultra-sleek, modern editorial graphic backdrop in dark mode 
        when no external image source is accessible.
        
        Guaranteed: Does NOT render any title text, badge text, or tofu boxes.
        Zero abstract glowing orbs or floating blobs.
        Acts as a pristine 1080x1080 canvas for PhotoCardRenderer.
        """
        width, height = 1080, 1080
        # Deep slate obsidian base
        image = Image.new("RGB", (width, height), color=(10, 15, 29))
        draw = ImageDraw.Draw(image)

        theme_colors = {
            "noon": ((14, 165, 233), (56, 189, 248)),    # Electric Sky Blue (AI Productivity)
            "night": ((16, 185, 129), (52, 211, 153))    # Emerald Green (B2B Automation)
        }
        primary_accent, secondary_accent = theme_colors.get(slot, theme_colors["noon"])

        # Modern deep slate vertical gradient
        for i in range(height):
            ratio = i / height
            r = int(10 + 6 * ratio)
            g = int(15 + 12 * ratio)
            b = int(29 + 25 * ratio)
            draw.line([(0, i), (width, i)], fill=(r, g, b))

        # Precision tech blueprint grid lines (very subtle)
        grid_step = 60
        for x in range(0, width, grid_step):
            draw.line([(x, 0), (x, height)], fill=(20, 28, 48), width=1)
        for y in range(0, height, grid_step):
            draw.line([(0, y), (width, y)], fill=(20, 28, 48), width=1)

        # High-tech diagonal circuit / data bus accent traces in lower-right corner
        for offset in [0, 20, 40]:
            draw.line([(width - 320 + offset, height), (width, height - 320 + offset)], fill=(25, 40, 68), width=2)

        # Sleek modern glassmorphic frame border
        margin = 40
        draw.rectangle([(margin, margin), (width - margin, height - margin)], outline=(30, 45, 75), width=2)

        # Accent corner brackets
        corner_len = 45
        # Top-left
        draw.line([(margin, margin), (margin + corner_len, margin)], fill=secondary_accent, width=4)
        draw.line([(margin, margin), (margin, margin + corner_len)], fill=secondary_accent, width=4)
        # Top-right
        draw.line([(width - margin, margin), (width - margin - corner_len, margin)], fill=secondary_accent, width=4)
        draw.line([(width - margin, margin), (width - margin, margin + corner_len)], fill=secondary_accent, width=4)
        # Bottom-left
        draw.line([(margin, height - margin), (margin + corner_len, height - margin)], fill=secondary_accent, width=4)
        draw.line([(margin, height - margin), (margin, height - margin - corner_len)], fill=secondary_accent, width=4)
        # Bottom-right
        draw.line([(width - margin, height - margin), (width - margin - corner_len, height - margin)], fill=secondary_accent, width=4)
        draw.line([(width - margin, height - margin), (width - margin, height - margin - corner_len)], fill=secondary_accent, width=4)

        # Subtle decorative tech horizontal beam
        draw.line([(margin, 380), (width - margin, 380)], fill=(25, 36, 56), width=1)
        draw.line([(margin + 80, 380), (margin + 200, 380)], fill=primary_accent, width=2)

        image.save(output_path, "JPEG", quality=95)
        logger.info(f"Sleek editorial fallback backdrop created at {output_path} (zero font text, pristine card canvas)")
        return output_path
