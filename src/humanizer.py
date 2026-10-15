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
    (r"(?im)^Here'?s (the thing|what happened|the secret|the takeaway)[:.]\s*", ""),
    (r"(?im)^The takeaway\?\s*", ""),
    (r"(?im)^ফলাফল কী\?\s*", ""),
    (r"(?im)^আসল ঘটনা কী\?\s*", ""),
    (r"(?im)^মজার বিষয় হলো[:.]\s*", ""),
]

# High-frequency AI cliches and natural replacements
AI_VOCAB_MAPPINGS = {
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

    def humanize(self, text: str) -> Dict[str, Any]:
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
        text = self.format_spacing(text)

        char_count = len(text)
        word_count = len(text.split())

        return {
            "humanized_text": text,
            "original_length": len(original),
            "final_length": char_count,
            "word_count": word_count,
            "vocab_cleaned": vocab_cleaned,
            "is_humanized": True
        }


# Global singleton helper
_humanizer = SocialPostHumanizer()

def humanize_post(text: str) -> Dict[str, Any]:
    """Helper function to run the humanizer pipeline on post copy."""
    return _humanizer.humanize(text)
