"""
Comprehensive Unit & Functional Verification Suite
Validates all components of the autonomous bot.
"""
import sys
import io

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
from src.config import (
    determine_current_slot,
    SLOTS,
    get_current_bst_time,
    GEMINI_API_KEY,
    FB_PAGE_ID,
    FB_PAGE_ACCESS_TOKEN
)
from src.history_manager import HistoryManager
from src.image_generator import ImageGenerator
from src.content_generator import ContentGenerator
from src.fb_client import FacebookClient

def test_config_and_time():
    print("🧪 [Test 1] Testing Timezone and Slot Logic...")
    from src.config import is_within_slot_window, SLOT_WINDOWS
    now_bst = get_current_bst_time()
    slot = determine_current_slot()
    print(f"  Current BST Time: {now_bst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Detected Slot: {slot} -> {SLOTS[slot]['theme']}")
    assert slot in ["morning", "noon", "afternoon", "night"]
    assert len(SLOT_WINDOWS) == 4, "Missing slot windows definitions!"
    print(f"  Within valid slot window for '{slot}': {is_within_slot_window(slot)}")
    print("  [OK] Time & Slot logic passed!\n")

def test_history_manager():
    print("🧪 [Test 2] Testing History Manager...")
    from src.config import TEMP_DIR
    test_history_path = TEMP_DIR / "test_history.json"
    hm = HistoryManager(history_file=test_history_path)
    
    if test_history_path.exists():
        test_history_path.unlink()

    hm.record_post(
        slot="morning",
        theme="Artificial Intelligence",
        title="টেস্ট টাইটেল ১",
        summary="এআই ভিত্তিক ডেটা অ্যানালাইসিস",
        post_id="12345"
    )
    
    history = hm.load_history()
    assert len(history) == 1
    assert history[0]["title"] == "টেস্ট টাইটেল ১"

    summary_text = hm.get_recent_topics_summary(slot="morning")
    print(f"  Summary Preview: {summary_text.strip()}")

    # Test Similarity Detection (Anti-duplicate)
    is_dup, matched = hm.check_similarity("টেস্ট টাইটেল ১", "এআই ডেটা অ্যানালাইসিস")
    assert is_dup is True, "Failed to catch duplicate topic!"
    print(f"  [OK] Successfully caught duplicate topic: '{matched}'")

    is_not_dup, _ = hm.check_similarity("কোয়ান্টাম কম্পিউটিং এর ভবিষ্যৎ", "সুপার কম্পিউটারের নতুন অগ্রগতি")
    assert is_not_dup is False, "False positive duplicate detected!"
    print("  [OK] Successfully approved unique new topic!")

    # Test Daily Slot Guard
    posted_today, ts = hm.is_slot_posted_today("morning")
    assert posted_today is True, "Failed to identify morning slot posted today!"
    not_posted, _ = hm.is_slot_posted_today("night")
    assert not_posted is False, "Identified night slot as posted when it was not!"
    print(f"  [OK] Successfully verified daily slot guard (Morning posted at {ts})")
    print("  [OK] History Manager passed!\n")

def test_image_generation():
    print("🧪 [Test 3] Testing AI Image Generation & Fallback...")
    ig = ImageGenerator()
    test_prompt = "Futuristic glowing AI neural network, cyan and purple cinematic light, photorealistic, 8k, no text"
    
    saved_path = ig.generate_image(
        prompt=test_prompt,
        title="AI Innovation",
        hero_keywords=["Artificial intelligence neural network", "Deep learning"],
        slot="morning"
    )
    assert saved_path is not None, "Image generation returned None!"
    assert saved_path.exists(), f"Image file not found at {saved_path}"
    file_size = saved_path.stat().st_size
    print(f"  [OK] Image generated at {saved_path} ({file_size:,} bytes)\n")

def test_gemini_content_generation():
    print("🧪 [Test 4] Testing Gemini Content Generator...")
    if not GEMINI_API_KEY:
        print("  ⚠️ GEMINI_API_KEY missing, skipping live API call.")
        return
    
    cg = ContentGenerator(api_key=GEMINI_API_KEY)
    post_data = cg.generate_post(slot="morning", recent_history_summary="")
    assert post_data.get("title"), "Post title is empty!"
    assert post_data.get("content"), "Post content is empty!"
    print(f"  [OK] Gemini Generated Title: {post_data.get('title')}")
    print(f"  [OK] Content Length: {len(post_data.get('content'))} characters\n")

def test_facebook_connection():
    print("🧪 [Test 5] Testing Facebook Page Connection & Token Health...")
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        print("  ⚠️ FB credentials missing, skipping Facebook check.")
        return
    
    fb = FacebookClient(page_id=FB_PAGE_ID, access_token=FB_PAGE_ACCESS_TOKEN)
    info = fb.verify_credentials()
    assert info.get("name"), "Failed to retrieve page name!"
    print(f"  [OK] Connected to Facebook Page: {info.get('name')} (ID: {info.get('id')})")
    print(f"  [OK] Token Expiration: {info.get('expires_at')} ({info.get('days_remaining')} days remaining)\n")

def test_photocard_rendering():
    print("🧪 [Test 6] Testing Editorial Photo Card Composition (Browser & Pillow Fail-Safe)...")
    from src.card_renderer import PhotoCardRenderer
    from src.config import BASE_DIR, TEMP_DIR
    renderer = PhotoCardRenderer()
    test_bg = TEMP_DIR / "latest_post_image.jpg"
    if not test_bg.exists():
        from PIL import Image
        img = Image.new("RGB", (1080, 1080), color=(15, 23, 42))
        img.save(test_bg)
    
    # 6a. Primary Rendering (Browser if available, or Pillow)
    card_path = renderer.render_photo_card(
        base_image_path=test_bg,
        headline="আর টাইপ করতে হবে না! স্ক্রিন দেখে কাজ করে দেয় এমন ৪টি এআই",
        category="Artificial Intelligence",
        highlight_words="এমন ৪টি এআই",
        slot="morning",
        output_path=TEMP_DIR / "test_runner_primary_card.jpg"
    )
    assert card_path is not None and card_path.exists(), "Primary PhotoCard rendering failed!"
    print(f"  [OK] Primary Photo Card generated at {card_path} ({card_path.stat().st_size:,} bytes)")

    # 6b. Guaranteed Pillow Fail-Safe Engine Test
    renderer_pillow = PhotoCardRenderer()
    renderer_pillow.browser_bin = None  # Force Pillow engine
    pillow_card_path = renderer_pillow.render_photo_card(
        base_image_path=test_bg,
        headline="আর টাইপ করতে হবে না! স্ক্রিন দেখে কাজ করে দেয় এমন ৪টি এআই",
        category="Artificial Intelligence",
        highlight_words="এমন ৪টি এআই",
        slot="morning",
        output_path=TEMP_DIR / "test_runner_pillow_fallback.jpg"
    )
    assert pillow_card_path is not None and pillow_card_path.exists(), "Pillow fail-safe rendering failed!"
    assert pillow_card_path.stat().st_size > 10000, "Pillow fail-safe output too small!"
    print(f"  [OK] Pillow Fail-Safe Photo Card verified at {pillow_card_path} ({pillow_card_path.stat().st_size:,} bytes)\n")

def main():
    print("=" * 60)
    print("🚀 AUTOMATED BOT COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 60)
    try:
        test_config_and_time()
        test_history_manager()
        test_image_generation()
        test_gemini_content_generation()
        test_facebook_connection()
        test_photocard_rendering()
        print("🎉 ALL 6 VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
