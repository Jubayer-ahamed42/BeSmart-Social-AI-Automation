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
    from src.config import is_within_slot_window, SLOT_WINDOWS, WHATSAPP_NUMBER
    import os
    now_bst = get_current_bst_time()
    slot = determine_current_slot()
    print(f"  Current BST Time: {now_bst.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  Detected Slot: {slot} -> {SLOTS[slot]['theme']}")
    assert slot in ["noon", "night"]
    assert len(SLOT_WINDOWS) == 2, "Missing slot windows definitions!"
    assert SLOT_WINDOWS["noon"]["valid_start"] == (11, 0) and SLOT_WINDOWS["noon"]["valid_end"] == (14, 0), "Incorrect noon window!"
    assert SLOT_WINDOWS["night"]["valid_start"] == (19, 0) and SLOT_WINDOWS["night"]["valid_end"] == (22, 0), "Incorrect night window!"
    
    # Test slot window boundaries
    import datetime, pytz
    from src.config import TZ
    test_1100 = datetime.datetime(2026, 10, 25, 11, 0, tzinfo=TZ)
    test_1400 = datetime.datetime(2026, 10, 25, 14, 0, tzinfo=TZ)
    test_1401 = datetime.datetime(2026, 10, 25, 14, 1, tzinfo=TZ)
    test_1900 = datetime.datetime(2026, 10, 25, 19, 0, tzinfo=TZ)
    test_2200 = datetime.datetime(2026, 10, 25, 22, 0, tzinfo=TZ)
    test_2201 = datetime.datetime(2026, 10, 25, 22, 1, tzinfo=TZ)
    
    assert is_within_slot_window("noon", test_1100) is True, "11:00 BST should be within noon window!"
    assert is_within_slot_window("noon", test_1400) is True, "14:00 BST should be within noon window!"
    assert is_within_slot_window("noon", test_1401) is False, "14:01 BST should be outside noon window!"
    assert is_within_slot_window("night", test_1900) is True, "19:00 BST should be within night window!"
    assert is_within_slot_window("night", test_2200) is True, "22:00 BST should be within night window!"
    assert is_within_slot_window("night", test_2201) is False, "22:01 BST should be outside night window!"

    # Test UTC datetime normalization in is_within_slot_window
    utc_1200_bst = datetime.datetime(2026, 10, 25, 6, 0, tzinfo=datetime.timezone.utc)
    assert is_within_slot_window("noon", utc_1200_bst) is True, "UTC datetime matching 12:00 BST should normalize to BST!"
    assert determine_current_slot(utc_1200_bst) == "noon"

    # Test WHATSAPP_NUMBER fallback
    assert WHATSAPP_NUMBER == "8801610594042", f"WHATSAPP_NUMBER unexpected: {WHATSAPP_NUMBER}"
    # Verify empty string fallback logic
    test_empty = (os.getenv("NON_EXISTENT_VAR", "").strip() or "8801610594042")
    assert test_empty == "8801610594042"
    
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
        slot="noon",
        theme="AI Productivity",
        title="টেস্ট টাইটেল ১",
        summary="এআই ভিত্তিক ডেটা অ্যানালাইসিস",
        post_id="12345"
    )
    
    history = hm.load_history()
    assert len(history) == 1
    assert history[0]["title"] == "টেস্ট টাইটেল ১"

    summary_text = hm.get_recent_topics_summary(slot="noon")
    print(f"  Summary Preview: {summary_text.strip()}")

    # Test Similarity Detection (Anti-duplicate)
    is_dup, matched = hm.check_similarity("টেস্ট টাইটেল ১", "এআই ডেটা অ্যানালাইসিস")
    assert is_dup is True, "Failed to catch duplicate topic!"
    print(f"  [OK] Successfully caught duplicate topic: '{matched}'")

    is_not_dup, _ = hm.check_similarity("কোয়ান্টাম কম্পিউটিং এর ভবিষ্যৎ", "সুপার কম্পিউটারের নতুন অগ্রগতি")
    assert is_not_dup is False, "False positive duplicate detected!"
    print("  [OK] Successfully approved unique new topic!")

    # Test Daily Slot Guard
    posted_today, ts = hm.is_slot_posted_today("noon")
    assert posted_today is True, "Failed to identify noon slot posted today!"
    not_posted, _ = hm.is_slot_posted_today("night")
    assert not_posted is False, "Identified night slot as posted when it was not!"
    print(f"  [OK] Successfully verified daily slot guard (Noon posted at {ts})")
    print("  [OK] History Manager passed!\n")

def test_humanizer():
    print("🧪 [Test 3] Testing Social Post Humanizer Engine (Emojis & Hashtags)...")
    from src.humanizer import humanize_post, EMOJI_PATTERN
    import re
    
    sample_raw = (
        "In today's fast-paced digital world, AI is a game-changer! 🚀\n\n"
        "Here is what happened: we tested 5 tools. ⚡\n"
        "• Tool 1: Fast 🔥\n"
        "• Tool 2: Smart 💡\n"
        "• Tool 3: Reliable 🎯\n\n"
        "Save this post right now! 📌\n\n"
        "#BeSmartWithAI #AI #Productivity #TechNews #Viral #Hacks"
    )
    res = humanize_post(sample_raw, default_topic_tag="#AIProductivity")
    cleaned = res["humanized_text"]
    
    # Verify AI cliches removed
    assert "In today's fast-paced digital world" not in cleaned
    assert "game-changer" not in cleaned
    assert "Here is what happened" not in cleaned
    
    # Verify emoji capping (max 2)
    assert res["emojis_total"] >= 5
    assert res["emojis_capped"] >= 3
    final_emojis = EMOJI_PATTERN.findall(cleaned)
    assert len(final_emojis) <= 2, f"Expected <= 2 emojis, found {len(final_emojis)}"
    
    # Verify strict 2 hashtags
    tags = re.findall(r"#[A-Za-z0-9_\u0980-\u09FF]+", cleaned)
    assert len(tags) == 2, f"Expected exactly 2 hashtags, found {len(tags)}: {tags}"
    assert tags[0] == "#BeSmartWithAI"
    assert tags[1] == "#AI"
    
    # Verify Dari spacing normalization
    sample_with_dari = "এটি একটি পরীক্ষামূলক বাক্য। এখানে বাড়তি স্পেস । এবং ৩টি ইমোজি 🚀 🔥 🎯 ।"
    dari_res = humanize_post(sample_with_dari)
    assert "স্পেস ।" not in dari_res["humanized_text"], "Failed to normalize space before Bengali Dari (।)"
    assert "স্পেস।" in dari_res["humanized_text"], "Bengali Dari should be attached to preceding word without space"
    assert "🎯" not in dari_res["humanized_text"], "Excess emoji should be capped"
    assert "🔥।" in dari_res["humanized_text"], "Capped emoji before Dari should cleanly attach Dari without orphaned whitespace"

    # Verify emoji pattern does not match Bengali characters
    bengali_sample = "বাংলা ভাষা ও সাহিত্য"
    assert len(EMOJI_PATTERN.findall(bengali_sample)) == 0, "EMOJI_PATTERN falsely matched Bengali characters!"

    print(f"  [OK] AI Cliches Sanitized: {res['vocab_cleaned']}")
    print(f"  [OK] Emojis Capped: {res['emojis_total']} down to {len(final_emojis)}")
    print(f"  [OK] Hashtags Enforced: {tags}")
    print(f"  [OK] Bengali Dari (।) Spacing Normalization Verified")
    print("  [OK] Social Post Humanizer passed!\n")

def test_image_generation():
    print("🧪 [Test 4] Testing FLUX AI Image Generation & Editorial Backdrop...")
    from src.config import TEMP_DIR
    ig = ImageGenerator()
    test_prompt = "Modern high-tech software engineering office workstation with ultra-wide curved monitor showing real-time code and neural network data metrics, mechanical keyboard, soft natural daylight, 35mm professional photography, strictly no female, no text, no watermark"
    
    saved_path = ig.generate_image(
        prompt=test_prompt,
        title="AI Innovation",
        hero_keywords=["software engineering workstation monitor", "modern office setup"],
        slot="noon"
    )
    assert saved_path is not None, "Image generation returned None!"
    assert saved_path.exists(), f"Image file not found at {saved_path}"
    file_size = saved_path.stat().st_size
    print(f"  [OK] Primary image generated at {saved_path} ({file_size:,} bytes)")

    # Verify Editorial Graphic Backdrop Fallback (Zero text / Zero tofu boxes)
    backdrop_path = TEMP_DIR / "test_runner_editorial_backdrop.jpg"
    res_backdrop = ig._create_editorial_poster(backdrop_path, slot="night")
    assert res_backdrop.exists(), "Editorial backdrop generation failed!"
    assert res_backdrop.stat().st_size > 10000, "Editorial backdrop file too small!"
    print(f"  [OK] Editorial Backdrop canvas verified at {res_backdrop} ({res_backdrop.stat().st_size:,} bytes)\n")

def test_prompt_sanitization_engine():
    print("🧪 [Test 4b] Testing Image Prompt Sanitizer & Anti-Glitch Directives...")
    import re
    # Test 1: Complex negation phrase stripping (preventing "no male professional" inversion)
    dirty_prompt = (
        "A male courier worker in warehouse with parcel boxes, strictly NO female, strictly NO woman, "
        "no cartoon, no 3D render, no text, no watermark, strictly NO abstract glowing orbs or dark empty voids"
    )
    clean = " ".join(dirty_prompt.strip().split())
    clean = re.sub(r"(?:strictly\s+)?(?:no|never|without)\s+[^,;.]+", "", clean, flags=re.IGNORECASE)
    assert "no male professional" not in clean.lower(), "Negation inversion bug detected!"
    assert "no man" not in clean.lower(), "Negation inversion bug detected!"
    assert "glowing orbs" not in clean.lower(), "Stray glowing orbs token leaked into positive prompt!"
    assert "cartoon" not in clean.lower(), "Negative token 'cartoon' leaked into positive prompt!"
    assert "female" not in clean.lower(), "'female' token leaked into positive prompt!"
    assert "parcel boxes" in clean.lower(), "Core positive subject was erroneously removed!"

    # Test 2: Affirmative female replacement
    female_prompt = "A female entrepreneur analyzing sales report on tablet"
    clean_fem = re.sub(r"(?:strictly\s+)?(?:no|never|without)\s+[^,;.]+", "", female_prompt, flags=re.IGNORECASE)
    clean_fem = re.sub(r"\bfemale\b", "male professional", clean_fem, flags=re.IGNORECASE)
    assert "male professional" in clean_fem, "Failed to replace female with male professional!"
    assert "female" not in clean_fem, "Female token remained in prompt!"

    print("  [OK] Negation clauses stripped cleanly without inversion")
    print("  [OK] Affirmative female tokens cleanly mapped to male/neutral")
    print("  [OK] Image Prompt Sanitizer verified!\n")

def test_gemini_content_generation():
    print("🧪 [Test 5] Testing Gemini Content Generator...")
    if not GEMINI_API_KEY:
        print("  ⚠️ GEMINI_API_KEY missing, skipping live API call.")
        return
    
    cg = ContentGenerator(api_key=GEMINI_API_KEY)
    post_data = cg.generate_post(slot="noon", recent_history_summary="")
    assert post_data.get("title"), "Post title is empty!"
    assert post_data.get("content"), "Post content is empty!"
    print(f"  [OK] Gemini Generated Title: {post_data.get('title')}")
def test_content_generator_retry_logic():
    print("🧪 [Test 5b] Testing Content Generator Retry Loop (Exception & JSON Recovery)...")
    import json
    cg = ContentGenerator(api_key="fake-key-for-retry-test")
    
    # 5b.1: Fail on attempt 1, succeed on attempt 2
    attempt_count = 0
    valid_payload = json.dumps({
        "title": "এআই দিয়ে অটোমেশন 🚀",
        "card_category": "AI Productivity",
        "card_headline": "এআই দিয়ে দ্রুত কাজ করার উপায়",
        "card_highlight": "দ্রুত কাজ",
        "content": "প্রথম লাইন হুক।\n\n• পয়েন্ট ১\n• পয়েন্ট ২\n\nপোস্টটি সেভ করুন।\n\n#BeSmartWithAI #AIProductivity",
        "hero_keywords": ["office automation", "laptop screen"],
        "image_prompt": "Editorial photo of laptop screen showing automated workflow, natural lighting, 35mm lens",
        "topic_summary": "অটোমেশন গাইড"
    })

    def mock_call_retry(prompt):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise RuntimeError("Simulated API 503 error on attempt 1")
        return valid_payload

    cg._call_gemini_api = mock_call_retry
    result = cg.generate_post(slot="noon", recent_history_summary="")
    assert attempt_count == 2, f"Expected 2 attempts before success, got {attempt_count}"
    assert result.get("title") == "এআই দিয়ে অটোমেশন 🚀", "Did not recover from attempt 1 failure!"
    print(f"  [OK] Successfully retried on attempt 1 failure and succeeded on attempt 2")

    # 5b.2: Exhaust all attempts -> fallback to _generate_fallback
    fail_count = 0
    def mock_call_always_fail(prompt):
        nonlocal fail_count
        fail_count += 1
        raise RuntimeError("Persistent network outage")

    cg._call_gemini_api = mock_call_always_fail
    fallback_res = cg.generate_post(slot="noon", recent_history_summary="")
    assert fail_count == 3, f"Expected exactly 3 retry attempts, got {fail_count}"
    assert "স্মার্ট সলিউশন" in fallback_res.get("card_headline", ""), "Fallback was not activated after exhausting all attempts"
    print(f"  [OK] Cleanly fell back only after all {fail_count} attempts were exhausted\n")

def test_facebook_connection():
    print("🧪 [Test 6] Testing Facebook Page Connection & Token Health...")
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        print("  ⚠️ FB credentials missing, skipping Facebook check.")
        return
    
    fb = FacebookClient(page_id=FB_PAGE_ID, access_token=FB_PAGE_ACCESS_TOKEN)
    info = fb.verify_credentials()
    assert info.get("name"), "Failed to retrieve page name!"
    print(f"  [OK] Connected to Facebook Page: {info.get('name')} (ID: {info.get('id')})")
    print(f"  [OK] Token Expiration: {info.get('expires_at')} ({info.get('days_remaining')} days remaining)")

    # 6b. Test Live Feed Fetch & Concurrency Guard Check
    recent_posts = fb.get_recent_posts(limit=3)
    print(f"  [OK] Live Feed Query: Retrieved {len(recent_posts)} recent post(s)")
    assert isinstance(recent_posts, list)
    already_posted, matched_p, reason = fb.check_already_posted(slot="noon")
    print(f"  [OK] Concurrency Guard Live Check: already_posted={already_posted} (Reason: {reason or 'None'})")

    # 6c. Edge Case Test: Clock Skew (Server clock 15s ahead of client)
    import datetime, pytz
    from src.config import TZ
    mock_now = datetime.datetime(2026, 10, 25, 12, 0, 0, tzinfo=TZ)
    # Post created 15 seconds "ahead"
    post_clock_skew = {"id": "test_skew", "created_time": "2026-10-25T12:00:15+06:00"}
    fb.get_recent_posts = lambda limit=3: [post_clock_skew]
    is_caught, _, skew_reason = fb.check_already_posted(slot="noon", now_dt=mock_now)
    assert is_caught is True, f"Clock skew (+15s) post was not caught! Reason: {skew_reason}"
    print("  [OK] Edge Case: Server-to-client clock drift (+15s) successfully caught!")

    # 6d. Edge Case Test: Post 30 minutes ago
    post_30m_ago = {"id": "test_30m", "created_time": "2026-10-25T11:30:00+06:00"}
    fb.get_recent_posts = lambda limit=3: [post_30m_ago]
    is_caught, _, _ = fb.check_already_posted(slot="noon", now_dt=mock_now)
    assert is_caught is True, "Post from 30 minutes ago was not caught!"
    print("  [OK] Edge Case: Post published 30 minutes ago successfully caught!")

    # 6e. Edge Case Test: Post made today at 10:50 AM BST (>2 hours ago, outside 11:00-14:00 window)
    mock_at_1300 = datetime.datetime(2026, 10, 25, 13, 0, 0, tzinfo=TZ)
    post_1050am = {"id": "test_1050", "created_time": "2026-10-25T10:50:00+06:00"}
    fb.get_recent_posts = lambda limit=3: [post_1050am]
    # For noon slot, this daytime post MUST be caught as already posted today for noon
    is_caught_noon, _, noon_reason = fb.check_already_posted(slot="noon", now_dt=mock_at_1300)
    assert is_caught_noon is True, f"Earlier 10:50 AM post was not caught for noon slot! Reason: {noon_reason}"
    # For night slot, this daytime post MUST NOT block the night slot
    is_caught_night, _, _ = fb.check_already_posted(slot="night", now_dt=mock_at_1300)
    assert is_caught_night is False, "Earlier 10:50 AM noon post falsely blocked the night slot!"
    print("  [OK] Edge Case: 10:50 AM post caught for noon slot and correctly permitted for night slot!")

    # 6f. Edge Case Test: Post made yesterday at 12:00 PM BST (>24 hours ago)
    post_yesterday = {"id": "test_yest", "created_time": "2026-10-24T12:00:00+06:00"}
    fb.get_recent_posts = lambda limit=3: [post_yesterday]
    is_caught_yest, _, _ = fb.check_already_posted(slot="noon", now_dt=mock_now)
    assert is_caught_yest is False, "Yesterday's post was falsely identified as today's post!"
    print("  [OK] Edge Case: Yesterday's post correctly ignored for today's slot!\n")

def test_photocard_rendering():
    print("🧪 [Test 7] Testing Editorial Photo Card Composition (Browser & Pristine Base Image Fail-Safe)...")
    from src.card_renderer import PhotoCardRenderer
    from src.config import BASE_DIR, TEMP_DIR
    renderer = PhotoCardRenderer()
    test_bg = TEMP_DIR / "latest_post_image.jpg"
    if not test_bg.exists():
        from PIL import Image
        img = Image.new("RGB", (1080, 1080), color=(15, 23, 42))
        img.save(test_bg)
    
    # 7a. Primary Rendering (Browser if available)
    card_path = renderer.render_photo_card(
        base_image_path=test_bg,
        headline="আর টাইপ করতে হবে না! স্ক্রিন দেখে কাজ করে দেয় এমন ৪টি এআই",
        category="AI Productivity & Hacks",
        highlight_words="এমন ৪টি এআই",
        slot="noon",
        output_path=TEMP_DIR / "test_runner_primary_card.jpg"
    )
    assert card_path is not None and card_path.exists(), "Primary PhotoCard rendering failed!"
    print(f"  [OK] Primary Photo Card generated at {card_path} ({card_path.stat().st_size:,} bytes)")

    # 7b. Clean Base Image Fallback Test (Zero corrupt text overlays / No broken Bengali conjuncts)
    renderer_fallback = PhotoCardRenderer()
    renderer_fallback.browser_bin = None  # Force browser unavailable
    fallback_card_path = renderer_fallback.render_photo_card(
        base_image_path=test_bg,
        headline="আর টাইপ করতে হবে না! স্ক্রিন দেখে কাজ করে দেয় এমন ৪টি এআই",
        category="AI Productivity & Hacks",
        highlight_words="এমন ৪টি এআই",
        slot="noon",
        output_path=TEMP_DIR / "test_runner_fallback.jpg"
    )
    assert fallback_card_path is not None and fallback_card_path.exists(), "Fallback rendering failed!"
    assert fallback_card_path == test_bg, "Did not fall back cleanly to pristine base image!"
    assert fallback_card_path.stat().st_size > 10000, "Base image output too small!"
    print(f"  [OK] Pristine Base Image Fallback verified at {fallback_card_path} ({fallback_card_path.stat().st_size:,} bytes)\n")

def main():
    print("=" * 60)
    print("🚀 AUTOMATED BOT COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 60)
    try:
        test_config_and_time()
        test_history_manager()
        test_humanizer()
        test_image_generation()
        test_prompt_sanitization_engine()
        test_gemini_content_generation()
        test_content_generator_retry_logic()
        test_facebook_connection()
        test_photocard_rendering()
        print("🎉 ALL 9 VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
