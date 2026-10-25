import datetime
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import requests
from src.config import FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

class FacebookClient:
    def __init__(self, page_id: str = None, access_token: str = None):
        self.page_id = (page_id or FB_PAGE_ID).strip()
        self.access_token = (access_token or FB_PAGE_ACCESS_TOKEN).strip()

    def verify_credentials(self) -> Dict[str, Any]:
        """
        Verifies if the Page ID and Page Access Token are valid.
        Returns Page details and token expiration info.
        """
        if not self.page_id or not self.access_token:
            raise ValueError("FB_PAGE_ID অথবা FB_PAGE_ACCESS_TOKEN পাওয়া যায়নি! দয়া করে .env বা GitHub Secrets সেট করুন।")

        # 1. Check Page Details
        url = f"{GRAPH_BASE_URL}/{self.page_id}"
        params = {
            "fields": "id,name,link",
            "access_token": self.access_token
        }
        try:
            res = requests.get(url, params=params, timeout=20)
            data = res.json()
            if res.status_code == 200:
                logger.info(f"Facebook Page Connected Successfully: {data.get('name')} (ID: {data.get('id')})")
            else:
                error_msg = data.get("error", {}).get("message", res.text)
                raise RuntimeError(f"ফেসবুক ভেরিফিকেশন ব্যর্থ হয়েছে: {error_msg}")
        except requests.RequestException as e:
            raise RuntimeError(f"ফেসবুক API সংযোগে ত্রুটি: {e}")

        # 2. Check Token Health / Expiration Info
        try:
            debug_url = f"{GRAPH_BASE_URL}/debug_token"
            debug_res = requests.get(debug_url, params={
                "input_token": self.access_token,
                "access_token": self.access_token
            }, timeout=15)
            debug_data = debug_res.json().get("data", {})
            expires_at = debug_data.get("expires_at", 0)
            data_access_expires_at = debug_data.get("data_access_expires_at", 0)

            if expires_at and expires_at > 0:
                exp_dt = datetime.datetime.fromtimestamp(expires_at)
                days_left = (exp_dt - datetime.datetime.now()).days
                data["expires_at"] = exp_dt.strftime("%Y-%m-%d %H:%M:%S")
                data["days_remaining"] = days_left
                logger.info(f"টোকেন অথেনটিকেশন মেয়াদ: {days_left} দিন বাকি (মেয়াদ শেষ: {data['expires_at']})")
            else:
                data["expires_at"] = "Never (স্থায়ী টোকেন)"
                data["days_remaining"] = 9999
                logger.info("টোকেন অথেনটিকেশন মেয়াদ: আজীবন স্থায়ী (Never Expires)")

            if data_access_expires_at and data_access_expires_at > 0:
                da_dt = datetime.datetime.fromtimestamp(data_access_expires_at)
                da_days = (da_dt - datetime.datetime.now()).days
                data["data_access_expires_at"] = da_dt.strftime("%Y-%m-%d %H:%M:%S")
                data["data_access_days_remaining"] = da_days
                if da_days <= 15:
                    logger.warning(f"⚠️ মেটা ডেটা এক্সেস পারমিশনের মেয়াদ সন্নিকটে: {da_days} দিন বাকি (নবায়ন: {data['data_access_expires_at']})")
                else:
                    logger.info(f"মেটা ডেটা এক্সেস পারমিশন উইন্ডো: {da_days} দিন বাকি ({data['data_access_expires_at']})")
        except Exception as e:
            logger.warning(f"Could not fetch token expiration details: {e}")

        return data

    def get_recent_posts(self, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Queries Facebook Page feed (GET /{page_id}/feed?limit=3) to fetch recent posts.
        Falls back to /{page_id}/published_posts or /{page_id}/posts if /feed requires extra permissions.
        Returns a list of post dicts with 'id', 'created_time', and optionally 'message'.
        """
        if not self.page_id or not self.access_token:
            return []

        endpoints = [
            f"{GRAPH_BASE_URL}/{self.page_id}/feed",
            f"{GRAPH_BASE_URL}/{self.page_id}/published_posts",
            f"{GRAPH_BASE_URL}/{self.page_id}/posts"
        ]
        params = {
            "fields": "id,created_time,message",
            "limit": limit,
            "access_token": self.access_token
        }

        for url in endpoints:
            try:
                res = requests.get(url, params=params, timeout=15)
                if res.status_code == 200:
                    data = res.json().get("data", [])
                    return data
                else:
                    logger.debug(f"Feed check on {url} returned status {res.status_code}: {res.text[:120]}")
            except Exception as e:
                logger.debug(f"Feed check error on {url}: {e}")

        return []

    def check_already_posted(
        self,
        slot: str,
        within_hours: float = 2.0,
        now_dt: Optional[datetime.datetime] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Checks real-time live Facebook Page feed to see if a post was already
        published on the Facebook Page today (matching the current slot) or within the last `within_hours`.
        Returns (already_posted: bool, matched_post: Optional[Dict], reason: str).
        """
        posts = self.get_recent_posts(limit=3)
        if not posts:
            return False, None, ""

        from src.config import TZ, is_within_slot_window, get_current_bst_time
        now_bst = now_dt or get_current_bst_time()

        for post in posts:
            ct_str = post.get("created_time", "")
            if not ct_str:
                continue
            try:
                # Handle ISO timestamps from Graph API (e.g. 2026-10-25T05:30:00+0000)
                if "+0000" in ct_str:
                    ct_str = ct_str.replace("+0000", "+00:00")
                post_dt = datetime.datetime.fromisoformat(ct_str)
                # Ensure aware in BST
                post_bst = post_dt.astimezone(TZ)
            except Exception as parse_err:
                logger.debug(f"Could not parse post created_time '{ct_str}': {parse_err}")
                continue

            # Check 1: Was it published within the last `within_hours`?
            time_diff_hours = (now_bst - post_bst).total_seconds() / 3600.0
            if 0 <= time_diff_hours < within_hours:
                post_time_str = post_bst.strftime('%Y-%m-%d %I:%M %p BST')
                return (
                    True,
                    post,
                    f"Post {post.get('id')} was published recently on Facebook Page ({time_diff_hours:.1f}h ago at {post_time_str}, within {within_hours}h guard)"
                )

            # Check 2: Was it published today in Bangladesh date matching the slot window?
            if post_bst.date() == now_bst.date() and is_within_slot_window(slot, post_bst):
                post_time_str = post_bst.strftime('%Y-%m-%d %I:%M %p BST')
                return (
                    True,
                    post,
                    f"Post {post.get('id')} was already published on Facebook Page today for slot '{slot}' at {post_time_str}"
                )

        return False, None, ""

    def publish_post(self, message: str, image_path: Optional[Path] = None) -> str:
        """
        Publishes a post to the Facebook Page.
        If an image_path is provided and exists, publishes a Photo with caption.
        Otherwise, publishes a standard Feed post (text-only).
        Returns the published Post ID.
        """
        if not self.page_id or not self.access_token:
            raise ValueError("FB_PAGE_ID অথবা FB_PAGE_ACCESS_TOKEN সেট করা নেই!")

        # If image is available, post photo
        if image_path and image_path.exists():
            return self._publish_photo_post(message, image_path)
        else:
            return self._publish_text_post(message)

    def _publish_photo_post(self, caption: str, image_path: Path) -> str:
        """Publishes photo with caption to the page."""
        url = f"{GRAPH_BASE_URL}/{self.page_id}/photos"
        logger.info(f"Publishing photo post to Facebook Page ({self.page_id})...")

        for attempt in range(2):
            try:
                with open(image_path, "rb") as img_file:
                    files = {
                        "source": img_file
                    }
                    data = {
                        "caption": caption,
                        "access_token": self.access_token
                    }
                    res = requests.post(url, files=files, data=data, timeout=60)
                    try:
                        result = res.json()
                    except Exception:
                        result = {}

                    if res.status_code == 200 and isinstance(result, dict):
                        post_id = result.get("post_id") or result.get("id")
                        if post_id:
                            logger.info(f"Photo post successfully published! Post ID: {post_id}")
                            return str(post_id)

                    error_data = result.get("error", {}) if isinstance(result, dict) else {}
                    error_msg = error_data.get("message", res.text[:200])
                    logger.warning(f"Photo post attempt {attempt+1} failed ({error_msg}).")
                    if attempt == 0:
                        time.sleep(3)
                        continue
                    logger.warning("Falling back to text post...")
                    return self._publish_text_post(caption)
            except Exception as e:
                logger.warning(f"Exception during photo upload (attempt {attempt+1}): {e}.")
                if attempt == 0:
                    time.sleep(3)
                    continue
                logger.warning("Falling back to text post...")
                return self._publish_text_post(caption)

        return self._publish_text_post(caption)

    def _publish_text_post(self, message: str) -> str:
        """Publishes text-only post to the page feed with retry."""
        url = f"{GRAPH_BASE_URL}/{self.page_id}/feed"
        logger.info(f"Publishing text feed post to Facebook Page ({self.page_id})...")

        payload = {
            "message": message,
            "access_token": self.access_token
        }
        for attempt in range(2):
            try:
                res = requests.post(url, data=payload, timeout=30)
                try:
                    result = res.json()
                except Exception:
                    result = {}

                if res.status_code == 200 and isinstance(result, dict):
                    post_id = result.get("id")
                    if post_id:
                        logger.info(f"Text post successfully published! Post ID: {post_id}")
                        return str(post_id)

                error_data = result.get("error", {}) if isinstance(result, dict) else {}
                error_msg = error_data.get("message", res.text[:200])
                error_code = error_data.get("code", res.status_code)
                logger.warning(f"Text post attempt {attempt+1} failed (Code {error_code}): {error_msg}")
                if attempt == 0:
                    time.sleep(3)
                    continue
                raise RuntimeError(f"ফেসবুকে পোস্ট পাবলিশ করতে ব্যর্থ (Code {error_code}): {error_msg}")
            except Exception as req_err:
                if attempt == 0:
                    time.sleep(3)
                    continue
                raise RuntimeError(f"ফেসবুক সার্ভার সংযোগ ত্রুটি: {req_err}")
