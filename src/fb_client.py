import datetime
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any
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
            expires_at = debug_data.get("expires_at")
            if expires_at and expires_at > 0:
                exp_dt = datetime.datetime.fromtimestamp(expires_at)
                days_left = (exp_dt - datetime.datetime.now()).days
                data["expires_at"] = exp_dt.strftime("%Y-%m-%d %H:%M:%S")
                data["days_remaining"] = days_left
                logger.info(f"টোকেন মেয়াদ: {days_left} দিন বাকি (মেয়াদ শেষ: {data['expires_at']})")
            else:
                data["expires_at"] = "Never (স্থায়ী টোকেন)"
                data["days_remaining"] = 9999
                logger.info("টোকেন মেয়াদ: আজীবন স্থায়ী (Never Expires)")
        except Exception as e:
            logger.warning(f"Could not fetch token expiration details: {e}")

        return data

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
