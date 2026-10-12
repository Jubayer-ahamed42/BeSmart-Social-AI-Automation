import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from src.config import HISTORY_FILE, get_current_bst_time

logger = logging.getLogger(__name__)

class HistoryManager:
    def __init__(self, history_file: Path = HISTORY_FILE):
        self.history_file = history_file

    def load_history(self) -> List[Dict[str, Any]]:
        """Loads previous posts history."""
        if not self.history_file.exists():
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.warning(f"Failed to read history file: {e}. Starting fresh.")
            return []

    def save_history(self, history: List[Dict[str, Any]]) -> None:
        """Saves history with a maximum limit of recent 250 entries atomically to prevent corruption."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            trimmed = history[-250:]
            temp_file = self.history_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(trimmed, f, ensure_ascii=False, indent=2)
            temp_file.replace(self.history_file)
        except Exception as e:
            logger.error(f"Failed to write history file: {e}")

    def record_post(self, slot: str, theme: str, title: str, summary: str, post_id: str = "", image_source: str = "") -> None:
        """Records a new post in the history including image source identifier."""
        history = self.load_history()
        now_str = get_current_bst_time().strftime("%Y-%m-%d %H:%M:%S BST")
        record = {
            "timestamp": now_str,
            "slot": slot,
            "theme": theme,
            "title": title,
            "summary": summary,
            "post_id": post_id,
            "image_source": image_source
        }
        history.append(record)
        self.save_history(history)
        logger.info(f"Recorded new post to history: '{title}' ({slot})")

    def get_used_image_sources(self, limit: int = 150) -> set:
        """Returns a set of image URLs or identifiers used in recent posts to prevent repeats."""
        history = self.load_history()
        used = set()
        for item in history[-limit:]:
            src = item.get("image_source", "")
            if src and src.strip():
                used.add(src.strip())
        return used

    def is_image_used(self, image_source: str) -> bool:
        """Checks if an image URL or identifier has been used recently."""
        if not image_source:
            return False
        return image_source.strip() in self.get_used_image_sources()

    def get_recent_topics_summary(self, slot: str = None, limit: int = 30) -> str:
        """
        Returns a formatted list of previous topics to feed into the AI prompt
        to prevent duplicate or repetitive content.
        """
        history = self.load_history()
        if not history:
            return "এখনো কোনো পূর্ববর্তী পোস্টের ইতিহাস নেই। নতুন বিষয়ে লিখো।"

        if slot:
            filtered = [item for item in history if item.get("slot") == slot]
        else:
            filtered = history

        recent = filtered[-limit:]
        if not recent:
            return "এই স্লটের জন্য এখনো কোনো পূর্ববর্তী পোস্ট রেকর্ড নেই।"

        lines = []
        for i, item in enumerate(recent, 1):
            title = item.get("title", "").strip()
            summary = item.get("summary", "").strip()
            lines.append(f"{i}. [পূর্বের পোস্ট]: {title} — ({summary})")

        return "\n".join(lines)

    def check_similarity(self, new_title: str, new_summary: str, threshold: float = 0.55) -> Tuple[bool, str]:
        """
        Determines if the new proposed topic is too similar to any previously posted topic.
        Uses token overlap / Jaccard similarity.
        Returns (is_duplicate: bool, matched_title: str).
        """
        history = self.load_history()
        if not history:
            return False, ""

        new_tokens = self._extract_tokens(f"{new_title} {new_summary}")
        if not new_tokens:
            return False, ""

        for past_item in history:
            past_title = past_item.get("title", "")
            past_summary = past_item.get("summary", "")
            past_tokens = self._extract_tokens(f"{past_title} {past_summary}")
            if not past_tokens:
                continue

            intersection = new_tokens.intersection(past_tokens)
            union = new_tokens.union(past_tokens)
            similarity = len(intersection) / len(union) if union else 0.0

            # Also check if title keywords are heavily overlapping (require at least 2 common tokens)
            title_tokens_new = self._extract_tokens(new_title)
            title_tokens_past = self._extract_tokens(past_title)
            title_intersection = title_tokens_new.intersection(title_tokens_past)
            if len(title_tokens_new) >= 2 and len(title_tokens_past) >= 2 and len(title_intersection) >= 2:
                title_overlap = len(title_intersection) / min(len(title_tokens_new), len(title_tokens_past))
            elif title_tokens_new and title_tokens_past and title_tokens_new == title_tokens_past:
                title_overlap = 1.0
            else:
                title_overlap = 0.0

            if similarity >= threshold or title_overlap >= 0.70:
                logger.warning(f"Duplicate/similar topic detected! Matches: '{past_title}' (Score: {similarity:.2f}, Title Overlap: {title_overlap:.2f})")
                return True, past_title

        return False, ""

    def _extract_tokens(self, text: str) -> set:
        """Extracts meaningful words in Bengali and English (length >= 3)."""
        clean = re.sub(r"[^\w\s\u0980-\u09FF]", " ", text.lower())
        words = clean.split()
        # Filter out common stop words and small particles
        stop_words = {
            "এই", "সেই", "কি", "কী", "কেন", "করে", "করা", "হবে", "হলে", "থেকে", "দিয়ে", "জন্য", "একটি", "দুটি",
            "and", "the", "for", "with", "this", "that", "from", "into", "best", "top"
        }
        return {w for w in words if len(w) >= 3 and w not in stop_words}

    def is_slot_recently_posted(self, slot: str, hours: float = 3.0) -> Tuple[bool, str]:
        """
        Checks if a post for this slot was already made within the last `hours`.
        Returns (is_recent: bool, last_timestamp: str).
        """
        history = self.load_history()
        if not history:
            return False, ""

        now_bst = get_current_bst_time().replace(tzinfo=None)
        for item in reversed(history):
            if item.get("slot") == slot:
                ts_str = item.get("timestamp", "")
                try:
                    dt_part = ts_str.split(" BST")[0].strip()
                    post_dt = datetime.strptime(dt_part, "%Y-%m-%d %H:%M:%S")
                    diff_hours = (now_bst - post_dt).total_seconds() / 3600.0
                    if 0 <= diff_hours < hours:
                        return True, ts_str
                    break
                except Exception:
                    pass
        return False, ""

    def is_slot_posted_today(self, slot: str, target_date: Optional[str] = None) -> Tuple[bool, str]:
        """
        Checks if a post for this slot has already been published today (in Bangladesh time).
        Guarantees that each slot (morning, noon, afternoon, night) is posted at most once per calendar day.
        Returns (is_posted_today: bool, last_timestamp: str).
        """
        history = self.load_history()
        if not history:
            return False, ""

        today_prefix = target_date or get_current_bst_time().strftime("%Y-%m-%d")
        for item in reversed(history):
            if item.get("slot") == slot:
                ts_str = item.get("timestamp", "")
                if ts_str.startswith(today_prefix):
                    return True, ts_str
        return False, ""

