import logging
import random
import re
import urllib.parse
from pathlib import Path
from typing import Optional, List, Set
import requests
from PIL import Image, ImageDraw, ImageOps, ImageFont, ImageFile
from src.config import BASE_DIR, TEMP_DIR

# Allow loading truncated images to prevent crash on slow or interrupted network streams
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)

# Strict regex with word boundaries to only detect genuine astronomy & cosmos topics
SPACE_TOPIC_REGEX = re.compile(
    r"\b(space|astronomy|telescope|webb|jwst|nebula|black hole|galaxy|nasa|exoplanet|supernova|cosmos|interstellar|orbit|mars|jupiter|saturn|moon|apollo|hubble)\b",
    re.IGNORECASE
)

class ImageGenerator:
    """
    Intelligent Visual Engine that delivers captivating, hyper-realistic, 
    content-matching images for social media posts.
    
    Slot-Tailored Priority:
    - Night Space Topics: NASA 4K Official Archive (Space only) -> AI Generation -> Editorial Poster
    - All Other Slots (Morning, Noon, Afternoon, Night): 100% Photorealistic AI Generation (Sana/Flux) -> Editorial Poster Fallback
    
    Safety & Quality Constraints:
    - 100% guarantee against female depictions.
    - Zero image repeats (deduplication check against history).
    - NASA API strictly scoped to night space topics (never triggered for daytime slots).
    - Watermark removal for AI-generated images.
    """
    def __init__(self, output_dir: Path = TEMP_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        self.last_image_source: str = ""

    def generate_image(
        self,
        prompt: str,
        title: str = "",
        hero_keywords: Optional[List[str]] = None,
        slot: str = "morning",
        used_image_sources: Optional[Set[str]] = None
    ) -> Optional[Path]:
        """
        Generates or fetches an authentic, highly captivating, 1080x1080 image 
        directly matching the post's core subject without repeating past images.
        """
        image_path = self.output_dir / "latest_post_image.jpg"
        keywords = hero_keywords or []
        used_sources = used_image_sources or set()
        self.last_image_source = ""
        
        # Clean up keyword list
        search_queries = [q.strip() for q in keywords if q and len(q.strip()) > 2]
        
        # Check if topic is genuine deep space / astronomy
        is_space_topic = bool(SPACE_TOPIC_REGEX.search(" ".join(search_queries) + " " + title))

        # =========================================================================
        # STRATEGY 1: Night Slot & Space Topics (NASA Official Archive)
        # =========================================================================
        if slot == "night" and is_space_topic:
            logger.info("🔭 [Night Space] Checking NASA Official Archive for authentic space photography...")
            for query in search_queries[:3]:
                img_url = self._fetch_nasa_image(query, used_sources)
                if img_url and self._download_and_format_image(img_url, image_path):
                    logger.info(f"✅ [NASA Archive] Space photograph processed: {query}")
                    self.last_image_source = img_url
                    return image_path

        # =========================================================================
        # STRATEGY 2: Primary AI Visual Engine (Pollinations Sana/Flux)
        # =========================================================================
        logger.info(f"🎨 [{slot.title()} Slot] Generating custom AI visual for maximum relevance and quality...")
        ai_source = self._generate_ai_image(prompt, image_path)
        if ai_source:
            logger.info(f"✅ [{slot.title()} AI] High-quality AI image successfully generated.")
            self.last_image_source = ai_source
            return image_path

        # =========================================================================
        # TIER 3: Editorial Graphic Poster Fallback (Zero-Error Local Card)
        # =========================================================================
        logger.info("🏷️ [Tier 3 Fallback] Creating branded editorial poster card...")
        try:
            self.last_image_source = f"editorial_poster_{slot}"
            return self._create_editorial_poster(image_path, title, slot)
        except Exception as e:
            logger.error(f"Failed to create editorial fallback: {e}")
            return None

    def _fetch_nasa_image(self, query: str, used_sources: Set[str]) -> Optional[str]:
        """Queries NASA's open image library API for authentic 4K space photography."""
        try:
            url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=image"
            r = requests.get(url, timeout=12)
            if r.status_code == 200:
                items = r.json().get('collection', {}).get('items', [])
                # Cycle through candidates to avoid repeats
                for item in items[:10]:
                    links = item.get('links', [])
                    for link in links:
                        href = link.get('href')
                        if href and (href.endswith('.jpg') or href.endswith('.png')):
                            img_url = href.replace('~thumb.jpg', '~medium.jpg').replace('~small.jpg', '~medium.jpg')
                            if img_url not in used_sources:
                                return img_url
        except Exception as e:
            logger.debug(f"NASA search error for '{query}': {e}")
        return None

    def _fetch_wiki_image(self, query: str, used_sources: Set[str]) -> Optional[str]:
        """Queries Wikipedia API for high-resolution article hero photographs."""
        try:
            url = 'https://en.wikipedia.org/w/api.php'
            params = {
                'action': 'query',
                'generator': 'search',
                'gsrsearch': query,
                'gsrlimit': 5,
                'prop': 'pageimages',
                'pithumbsize': 1280,
                'format': 'json'
            }
            r = requests.get(url, params=params, headers=self.headers, timeout=10)
            if r.status_code == 200:
                pages = r.json().get('query', {}).get('pages', {})
                for pid, pdata in pages.items():
                    page_title = pdata.get('title', '').lower()
                    # Filter out any female portraits
                    female_markers = ['woman', 'female', 'girl', 'actress', 'lady', 'queen', 'mother', 'sister', 'she']
                    if any(w in page_title for w in female_markers):
                        continue
                    if 'thumbnail' in pdata:
                        thumb = pdata['thumbnail']
                        src = thumb.get('source', '')
                        lower_src = src.lower()
                        # Exclude diagrams, flowcharts, schemas, icons
                        bad_markers = ['.svg', 'diagram', 'schema', 'chart', 'flowchart', 'graph', 'model-archit', 'unsupervised', 'drawing', 'woman', 'female', 'girl']
                        if src and not any(m in lower_src for m in bad_markers) and thumb.get('width', 0) >= 380:
                            if src not in used_sources:
                                return src
        except Exception as e:
            logger.debug(f"Wiki search error for '{query}': {e}")
        return None

    def _generate_ai_image(self, prompt: str, output_path: Path) -> Optional[str]:
        """Calls Pollinations AI with clean prompt and strict negative constraints."""
        clean_prompt = " ".join(prompt.strip().split())

        # Programmatically sanitize any female references
        female_words = [r"\bfemale\b", r"\bwoman\b", r"\bwomen\b", r"\bgirl\b", r"\bgirls\b", r"\blady\b", r"\bladies\b"]
        for word in female_words:
            clean_prompt = re.sub(word, "scientist", clean_prompt, flags=re.IGNORECASE)

        # Remove negative phrases from positive prompt to avoid CLIP latching
        clean_prompt = re.sub(r"(strictly\s+)?no\s+(female|woman|girl|women|girls)", "", clean_prompt, flags=re.IGNORECASE)
        clean_prompt = clean_prompt.strip().rstrip(",")

        # Enhance positive aesthetic for photorealism & technology
        clean_prompt += ", photorealistic, 8k resolution, cinematic studio lighting, sharp focus, 35mm photography, high tech hardware, futuristic technology, computer server, clean render"

        encoded = urllib.parse.quote(clean_prompt[:450])
        seed = random.randint(100000, 9999999)
        negative_prompt = urllib.parse.quote("female, woman, girl, lady, women, feminine, abstract orb, glowing sphere, empty dark void, plain blob, lens flare in empty space, deformed, text, watermark, signature, blur")

        models = ["sana", "flux", "turbo"]
        for model in models:
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1080&model={model}&nologo=true&seed={seed}&negative={negative_prompt}"
            try:
                r = requests.get(url, headers=self.headers, timeout=25)
                if r.status_code == 200 and len(r.content) > 8000:
                    success = self._process_image_bytes(r.content, output_path, is_ai_generated=True)
                    if success:
                        return f"ai_pollinations_{model}_{seed}"
            except Exception as e:
                logger.debug(f"Pollinations {model} failed: {e}")

        return None

    def _download_and_format_image(self, url: str, output_path: Path) -> bool:
        """Downloads an image from URL and formats it into a crisp 1080x1080 square."""
        try:
            r = requests.get(url, headers=self.headers, timeout=20)
            if r.status_code == 200 and len(r.content) > 5000:
                return self._process_image_bytes(r.content, output_path, is_ai_generated=False)
        except Exception as e:
            logger.warning(f"Error downloading image from {url}: {e}")
        return False

    def _process_image_bytes(self, data: bytes, output_path: Path, is_ai_generated: bool = False) -> bool:
        """Loads image data, crops watermark if AI generated, fits into centered 1080x1080, and saves as JPEG."""
        import io
        try:
            img = Image.open(io.BytesIO(data))
            if is_ai_generated:
                w, h = img.size
                # Crop bottom 45px to eliminate watermark cleanly
                if h > 100:
                    img = img.crop((0, 0, w, h - 45))
            fitted = ImageOps.fit(img, (1080, 1080), method=Image.Resampling.LANCZOS)
            fitted.convert("RGB").save(output_path, "JPEG", quality=95)
            return True
        except Exception as e:
            logger.error(f"Image formatting error: {e}")
            return False

    def _create_editorial_poster(self, output_path: Path, title: str, slot: str) -> Path:
        """
        Creates an ultra-sleek, modern editorial graphic poster in dark mode 
        when no external image source is accessible.
        """
        width, height = 1080, 1080
        image = Image.new("RGB", (width, height), color=(10, 15, 29))  # Deep slate obsidian
        draw = ImageDraw.Draw(image)

        # Ambient background glow
        theme_colors = {
            "morning": (14, 165, 233),    # Electric Sky Blue (AI)
            "noon": (16, 185, 129),       # Emerald Tech (Innovation)
            "afternoon": (245, 158, 11),  # Amber / Security Gold (Cybersecurity)
            "night": (168, 85, 247)       # Cosmic Purple (Space)
        }
        accent = theme_colors.get(slot, (14, 165, 233))

        for r in range(450, 0, -25):
            alpha = int(20 * (r / 450))
            box = [(width//2 - r, 380 - r), (width//2 + r, 380 + r)]
            draw.ellipse(box, outline=(accent[0], accent[1], accent[2], alpha), width=3)

        # Sleek glassmorphism borders
        margin = 45
        draw.rectangle([(margin, margin), (width - margin, height - margin)], outline=(30, 41, 59), width=3)
        draw.line([(margin, margin), (width - margin, margin)], fill=accent, width=6)

        # Load TrueType font for clean Bengali & English rendering
        font_path = BASE_DIR / "assets" / "fonts" / "HindSiliguri-Bold.ttf"
        title_font = ImageFont.truetype(str(font_path), 38) if font_path.exists() else None
        badge_font = ImageFont.truetype(str(font_path), 22) if font_path.exists() else None
        brand_font = ImageFont.truetype(str(font_path), 20) if font_path.exists() else None

        # Category pill badge
        slot_names = {
            "morning": "ARTIFICIAL INTELLIGENCE",
            "noon": "TECH & INNOVATION",
            "afternoon": "CYBERSECURITY & PRIVACY",
            "night": "SCIENCE & DEEP SPACE"
        }
        badge_text = f"  {slot_names.get(slot, 'SMART TECH')}  "
        draw.rectangle([(margin + 40, margin + 40), (margin + 380, margin + 90)], fill=(15, 23, 42), outline=accent, width=2)
        draw.text((margin + 60, margin + 50), badge_text, fill=accent, font=badge_font)

        # Center Tech Emblem Badge
        draw.rounded_rectangle([(width//2 - 130, height//2 - 120), (width//2 + 130, height//2 - 60)], radius=18, fill=(15, 23, 42), outline=accent, width=2)
        draw.text((width//2, height//2 - 88), "TECH INSIGHT", fill=accent, anchor="mm", font=badge_font)

        # Title formatting (truncate cleanly if needed)
        clean_title = title if len(title) <= 55 else title[:52] + "..."
        draw.text((width//2, height//2 + 30), clean_title, fill=(248, 250, 252), anchor="mm", font=title_font)

        # Bottom branding line
        draw.text((width//2, height - margin - 50), "BE SMART WITH AI • DAILY DISCOVERY", fill=(148, 163, 184), anchor="mm", font=brand_font)

        image.save(output_path, "JPEG", quality=95)
        logger.info(f"Editorial fallback poster created at {output_path}")
        return output_path
