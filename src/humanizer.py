"""
Hybrid Post Humanizer Engine V3 (Facebook & Social Media)
Combines LinkedIn Humanizer V3 stylometry rules with Fabric-style zero-fluff text processing.
Cleans AI detection fingerprints, reveal bridges, em-dash clutter, and forensic markers.
"""

import re
import logging
from typing import Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

# Forensic leakage markers that should never appear in published posts
FORENSIC_PATTERNS = [
    r"\boaicite\b",
    r"\bcontentReference\b",
    r"\bturn\d+search\d+\b",
    r"\battached_file\b",
    r"\bgrok_card\b",
    r"As of my (last update|knowledge cutoff)[^.]*\.",
    r"\[Your Name\]",
    r"\[Your Company\]",
    r"\[Insert [^]]+\]",
    r"\[Describe [^]]+\]",
]

# Reveal bridges that kill mobile dwell-time and trigger algorithm penalties
REVEAL_BRIDGES = [
    (r"(?im)^The (result|outcome|lesson|catch|truth|kicker)\?\s*", ""),
    (r"(?im)^Plot twist:\s*", ""),
    (r"(?im)^Here('?s|\s+is) (the thing|what happened|the secret|the takeaway)[:.]\s*", ""),
    (r"(?im)^The takeaway\?\s*", ""),
    (r"(?im)^ফলাফল কী\?\s*", ""),
    (r"(?im)^আসল ঘটনা কী\?\s*", ""),
    (r"(?im)^মজার বিষয় হলো[:.]\s*", ""),
]

# High-frequency AI cliches and natural replacements
AI_VOCAB_MAPPINGS = {
    r"\bin today's fast[- ]paced (digital )?world\b": "today",
    r"\bdelve into\b": "explore",
    r"\bdelve\b": "look into",
    r"\btapestry\b": "mix",
    r"\brevolutioniz(e|es|ed|ing)\b": "transform",
    r"\bgame[- ]changer\b": "breakthrough",
    r"\bfurthermore\b": "also",
    r"\bit is important to note that\b": "keep in mind,",
    r"\bit is worth noting that\b": "notably,",
    r"\bleverag(e|es|ed|ing)\b": "use",
    r"\bstreamlin(e|es|ed|ing)\b": "simplify",
    r"\bholistic\b": "complete",
    r"\bmultifaceted\b": "varied",
    r"\brobust\b": "strong",
    r"\bseamlessly\b": "smoothly",
    r"\bseamless\b": "smooth",
    r"\bfoster(s|ed|ing)?\b": "build",
    r"\btestament to\b": "proof of",
    r"\blet that sink in\b": "",
    r"আজকের দ্রুত পরিবর্তনশীল বিশ্বে": "বর্তমানে",
    r"ডিজিটাল যুগের এই সময়ে": "আজকের দিনে",
}

# Unicode emoji regex that covers all standard emoji ranges
EMOJI_PATTERN = re.compile(
    r"["
    r"\U0001F600-\U0001F64F"  # emoticons
    r"\U0001F300-\U0001F5FF"  # symbols & pictographs
    r"\U0001F680-\U0001F6FF"  # transport & map symbols
    r"\U0001F1E0-\U0001F1FF"  # flags (iOS)
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    r"\U00002702-\U000027B0"  # Dingbats
    r"\U000024C2-\U0001F251" 
    r"\U00002600-\U000026FF"  # Misc symbols
    r"\U00002B00-\U00002BFF"
    r"\uFE0F"
    r"]+"
)


class SocialPostHumanizer:
    """Post-processor that transforms AI drafts into authentic, high-converting social copy."""

    def __init__(self, mode: str = "strict"):
        self.mode = mode

    def clean_forensic_markers(self, text: str) -> str:
        """Removes model leakage, AI placeholders, and cutoff disclaimers."""
        for pattern in FORENSIC_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text

    def clean_reveal_bridges(self, text: str) -> str:
        """Removes formulaic AI reveal bridges and transitions."""
        for pattern, replacement in REVEAL_BRIDGES:
            text = re.sub(pattern, replacement, text)
        return text

    def calibrate_em_dashes(self, text: str, max_allowed: int = 2) -> str:
        """
        Caps em-dashes at max 1-2 per post.
        Excess em-dashes are converted to natural commas or colons.
        """
        em_count = text.count("—")
        if em_count <= max_allowed:
            return text

        parts = text.split("—")
        result = [parts[0]]
        for i, part in enumerate(parts[1:], 1):
            if i < max_allowed:
                result.append("—" + part)
            else:
                sep = ": " if i == max_allowed else ", "
                result.append(sep + part.lstrip())
        return "".join(result)

    def normalize_punctuation(self, text: str) -> str:
        """Normalizes curly quotes, double hyphens, and whitespace."""
        text = text.replace("“", '"').replace("”", '"')
        text = text.replace("‘", "'").replace("’", "'")
        text = re.sub(r"\s*--\s*", ", ", text)
        return text

    def scrub_ai_vocabulary(self, text: str) -> Tuple[str, List[str]]:
        """Replaces AI vocabulary and returns list of cleaned terms."""
        replaced_terms = []
        for pattern, replacement in AI_VOCAB_MAPPINGS.items():
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                replaced_terms.extend([m if isinstance(m, str) else m[0] for m in matches])
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text, replaced_terms

    def format_spacing(self, text: str) -> str:
        """Ensures mobile-optimized spacing (1-2 lines per paragraph)."""
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        return "\n\n".join(paragraphs)

    def cap_emojis(self, text: str, max_allowed: int = 2) -> Tuple[str, int]:
        """
        Caps total emojis in the post to maximum allowed (default: 2).
        Excess emojis are cleanly removed and spacing normalized.
        Prevents algorithmic spam penalty while keeping authentic human touch.
        """
        count = 0
        def repl(m):
            nonlocal count
            count += 1
            return m.group(0) if count <= max_allowed else ""

        cleaned = EMOJI_PATTERN.sub(repl, text)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r" ([.,!?:;])", r"\1", cleaned)
        lines = [line.strip() for line in cleaned.split("\n")]
        return "\n".join(lines), count

    def enforce_strict_two_hashtags(self, text: str, default_topic_tag: str = "#BusinessAutomation") -> str:
        """
        Enforces Meta's optimal algorithm policy:
        Strictly maximum 2 hashtags:
        - 1st: #BeSmartWithAI
        - 2nd: Topic hashtag (extracted from post or default_topic_tag)
        Strips away any 3rd, 4th, 5th+ hashtags to protect organic reach.
        """
        tags = re.findall(r"#[A-Za-z0-9_\u0980-\u09FF]+", text)

        # Remove trailing empty lines and trailing hashtag lines safely
        lines = text.strip().splitlines()
        while lines and (not lines[-1].strip() or lines[-1].strip().startswith("#")):
            lines.pop()
        clean_body = "\n".join(lines).strip()

        primary_tag = "#BeSmartWithAI"
        secondary_tag = default_topic_tag

        # Find first non-primary tag to use as topic tag
        for tag in tags:
            if tag.lower() != primary_tag.lower():
                secondary_tag = tag
                break

        return f"{clean_body}\n\n{primary_tag} {secondary_tag}"

    def humanize(self, text: str, default_topic_tag: str = "#BusinessAutomation") -> Dict[str, Any]:
        """
        Executes complete multi-pass humanization pipeline on a Facebook post.
        Returns cleaned text, metadata, and audit summary.
        """
        original = text
        text = self.clean_forensic_markers(text)
        text = self.clean_reveal_bridges(text)
        text = self.normalize_punctuation(text)
        text, vocab_cleaned = self.scrub_ai_vocabulary(text)
        text = self.calibrate_em_dashes(text)
        text, emojis_found = self.cap_emojis(text, max_allowed=2)
        text = self.format_spacing(text)
        text = self.enforce_strict_two_hashtags(text, default_topic_tag=default_topic_tag)

        char_count = len(text)
        word_count = len(text.split())

        return {
            "humanized_text": text,
            "original_length": len(original),
            "final_length": char_count,
            "word_count": word_count,
            "vocab_cleaned": vocab_cleaned,
            "emojis_total": emojis_found,
            "emojis_capped": max(0, emojis_found - 2),
            "is_humanized": True
        }


# Global singleton helper
_humanizer = SocialPostHumanizer()

def humanize_post(text: str, default_topic_tag: str = "#BusinessAutomation") -> Dict[str, Any]:
    """Helper function to run the humanizer pipeline on post copy."""
    return _humanizer.humanize(text, default_topic_tag=default_topic_tag)
