import argparse
import logging
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
    SLOTS,
    SLOT_WINDOWS,
    is_within_slot_window,
    determine_current_slot,
    get_current_bst_time,
    GEMINI_API_KEY,
    FB_PAGE_ID,
    FB_PAGE_ACCESS_TOKEN
)
from src.history_manager import HistoryManager
from src.content_generator import ContentGenerator
from src.image_generator import ImageGenerator
from src.card_renderer import PhotoCardRenderer
from src.fb_client import FacebookClient

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("FB_AUTO_POSTER")

def run_poster(slot: str = "auto", dry_run: bool = False, skip_image: bool = False, force: bool = False) -> None:
    now_bst = get_current_bst_time()
    logger.info("=" * 60)
    logger.info("🤖 শুরু হচ্ছে ফেসবুক অটোপোস্টিং স্বয়ংক্রিয় বট")
    logger.info(f"⏰ বর্তমান সময় (বাংলাদেশ): {now_bst.strftime('%Y-%m-%d %I:%M:%S %p')} BST")

    # 1. Determine Slot
    if not slot or slot == "auto":
        slot = determine_current_slot()
    
    if slot not in SLOTS:
        logger.warning(f"স্লট '{slot}' পাওয়া যায়নি, ডিফল্ট 'morning' নির্বাচন করা হলো।")
        slot = "morning"

    slot_info = SLOTS[slot]
    logger.info(f"🎯 নির্বাচিত স্লট: {slot_info['name']}")
    logger.info(f"📌 বিষয়বস্তু (Theme): {slot_info['theme']}")
    logger.info("=" * 60)

    # 2. History & Timing Guards
    history_mgr = HistoryManager()

    # 2.1 Daily Slot Guard (গ্যারান্টি: প্রতিটি স্লটে দিনে সর্বোচ্চ একবারই পোস্ট হবে)
    if not dry_run and not force:
        already_posted, last_ts = history_mgr.is_slot_posted_today(slot=slot)
        if already_posted:
            logger.warning(f"⚠️ স্লট '{slot}' এর জন্য আজকের দিনে ইতিমধ্যে পোস্ট করা হয়েছে ({last_ts})।")
            logger.info("🛡️ ডাবল/ডুপ্লিকেট রান প্রতিরোধ সক্রিয়: আজকের জন্য এই স্লটটি স্কিপ করা হলো (ফোর্স করতে --force ব্যবহার করুন)।")
            return

        # 2.2 Stale Run Guard (যদি গিটহাব অ্যাকশন্সের কিউ অতিরিক্ত দেরিতে ওয়েকআপ করে, তবে আউট-অফ-উইন্ডো পোস্ট প্রতিরোধ)
        if not is_within_slot_window(slot, now_bst):
            window_info = SLOT_WINDOWS.get(slot, {})
            v_start = f"{window_info.get('valid_start', (0,0))[0]:02d}:{window_info.get('valid_start', (0,0))[1]:02d}"
            v_end = f"{window_info.get('valid_end', (0,0))[0]:02d}:{window_info.get('valid_end', (0,0))[1]:02d}"
            logger.warning(
                f"⚠️ শিডিউল ডিলে শনাক্ত: স্লট '{slot}' রান শুরু হয়েছে {now_bst.strftime('%I:%M %p')} BST এ, "
                f"যা অনুমোদিত উইন্ডোর ({v_start} - {v_end} BST) বাইরে।"
            )
            logger.info("🛡️ অসময়ে পোস্ট হওয়া ঠেকাতে এই বিলম্বিত রানটি স্কিপ করা হলো (ফোর্স করতে --force ব্যবহার করুন)।")
            return

    recent_summary = history_mgr.get_recent_topics_summary(slot=slot, limit=30)
    logger.info(f"📚 পূর্ববর্তী পোস্টের ইতিহাস লোড হয়েছে। ডুপ্লিকেট টপিক প্রতিরোধ সক্রিয়।")

    # 3. কন্টেন্ট জেনারেশন (Google Gemini AI + Anti-duplicate Verification)
    logger.info("✍️ Gemini AI দিয়ে নতুন এবং শিক্ষণীয় বাংলা পোস্ট তৈরি করা হচ্ছে...")
    content_gen = ContentGenerator(api_key=GEMINI_API_KEY)
    
    try:
        post_data = content_gen.generate_post(
            slot=slot,
            recent_history_summary=recent_summary,
            history_mgr=history_mgr
        )
    except Exception as e:
        logger.error(f"❌ কন্টেন্ট জেনারেশনে সমস্যা: {e}")
        sys.exit(1)

    title = post_data.get("title", "")
    content = post_data.get("content", "")
    image_prompt = post_data.get("image_prompt", "")
    topic_summary = post_data.get("topic_summary", "")
    hero_keywords = post_data.get("hero_keywords", [])

    logger.info(f"✅ কন্টেন্ট তৈরি সম্পন্ন: '{title}'")
    logger.info(f"📝 সংক্ষেপ: {topic_summary}")
    if hero_keywords:
        logger.info(f"🔍 হিরো কী-ওয়ার্ড: {hero_keywords}")

    # 4. ইমেজ জেনারেশন (Multi-Tier Visual Engine)
    image_path = None
    img_gen = None
    image_src = ""
    if not skip_image and (image_prompt or hero_keywords):
        logger.info("🎨 মাল্টি-টিয়ার ভিজ্যুয়াল ইঞ্জিন চালু হচ্ছে...")
        if image_prompt:
            logger.info(f"🖼️ ইমেজ প্রম্পট: {image_prompt[:120]}...")
        img_gen = ImageGenerator()
        used_image_sources = history_mgr.get_used_image_sources()
        image_path = img_gen.generate_image(
            prompt=image_prompt,
            title=title,
            hero_keywords=hero_keywords,
            slot=slot,
            used_image_sources=used_image_sources
        )
        if image_path:
            image_src = img_gen.last_image_source
            logger.info(f"✅ ব্যাকগ্রাউন্ড ছবি প্রস্তুত হয়েছে: {image_path} (উৎস: {image_src})")
            # 4.1 ফটোকার্ড কম্পোজিশন (Editorial Photo Card with Bengali Subtitle)
            try:
                card_headline = post_data.get("card_headline") or title
                card_category = post_data.get("card_category", "")
                card_highlight = post_data.get("card_highlight", "")

                logger.info("🖼️ ফটোকার্ড কম্পোজিশন শুরু হচ্ছে (বাংলা সাবটাইটেল ও ব্র্যান্ডিং সহ)...")
                card_renderer = PhotoCardRenderer()
                card_output_path = image_path.with_name("latest_post_photocard.jpg")
                final_card_path = card_renderer.render_photo_card(
                    base_image_path=image_path,
                    headline=card_headline,
                    category=card_category,
                    highlight_words=card_highlight,
                    slot=slot,
                    output_path=card_output_path
                )
                image_path = final_card_path
                logger.info(f"📸 চূড়ান্ত ফটোকার্ড সফলভাবে তৈরি হয়েছে: {image_path}")
            except Exception as e:
                logger.warning(f"ফটোকার্ড রেন্ডারিং ব্যর্থ, মূল ব্যাকগ্রাউন্ড ছবি ব্যবহার করা হবে: {e}")
        else:
            logger.warning("⚠️ ছবি তৈরি ব্যর্থ হয়েছে, টেক্সট পোস্ট হিসেবে প্রকাশ করা হবে।")

    # 5. প্রিভিউ প্রদর্শন
    print("\n" + "=" * 30 + " [পোস্ট প্রিভিউ] " + "=" * 30)
    print(content)
    print("=" * 77 + "\n")

    # 6. পাবলিশিং অথবা ড্রাই-রান
    if dry_run:
        logger.info("🧪 [DRY-RUN মোড সক্রিয়] ফেসবুকে কোনো পোস্ট পাঠানো হয়নি। প্রিভিউ ও ইমেজ সফলভাবে জেনারেট হয়েছে।")
        return

    # ফেসবুকে পোস্ট পাঠানো
    logger.info("🚀 Meta Graph API দিয়ে ফেসবুক পেজে পোস্ট পাঠানো হচ্ছে...")
    fb_client = FacebookClient(page_id=FB_PAGE_ID, access_token=FB_PAGE_ACCESS_TOKEN)
    
    try:
        post_id = fb_client.publish_post(message=content, image_path=image_path)
        logger.info(f"🎉 পোস্ট সফলভাবে ফেসবুকে প্রকাশিত হয়েছে! পোস্ট আইডি: {post_id}")

        # 7. হিস্ট্রি আপডেট
        history_mgr.record_post(
            slot=slot,
            theme=slot_info["theme"],
            title=title,
            summary=topic_summary,
            post_id=str(post_id),
            image_source=image_src
        )
        logger.info("💾 হিস্ট্রি আপডেট করা হয়েছে। পরবর্তী পোস্টে এই বিষয় ও ছবি পুনরাবৃত্তি হবে না।")

    except Exception as e:
        logger.error(f"❌ ফেসবুকে পোস্ট করতে ত্রুটি ঘটেছে: {e}")
        sys.exit(1)

def verify_credentials() -> None:
    """Verifies API credentials without making posts."""
    logger.info("🔍 ক্রেডেনশিয়াল ভেরিফিকেশন শুরু হচ্ছে...")
    
    # 1. Gemini
    print("\n[১] Google Gemini API চেক:")
    if not GEMINI_API_KEY:
        print("  ❌ GEMINI_API_KEY পাওয়া যায়নি (.env বা Environment Variables চেক করুন)")
    else:
        print("  🔑 GEMINI_API_KEY পাওয়া গেছে। টেস্ট কল করা হচ্ছে...")
        try:
            gen = ContentGenerator(api_key=GEMINI_API_KEY)
            res = gen.generate_post(slot="morning", recent_history_summary="")
            print(f"  ✅ Gemini API সফলভাবে সংযুক্ত! শিরোনাম: {res.get('title')}")
        except Exception as e:
            print(f"  ❌ Gemini API ত্রুটি: {e}")

    # 2. Facebook
    print("\n[২] Facebook Page Credentials চেক:")
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        print("  ❌ FB_PAGE_ID অথবা FB_PAGE_ACCESS_TOKEN মিসিং!")
    else:
        print(f"  🔑 FB_PAGE_ID: {FB_PAGE_ID}")
        print("  📡 মেটা গ্রাফ এপিআই কানেকশন টেস্ট করা হচ্ছে...")
        try:
            fb = FacebookClient(page_id=FB_PAGE_ID, access_token=FB_PAGE_ACCESS_TOKEN)
            info = fb.verify_credentials()
            print(f"  ✅ ফেসবুক পেজ সফলভাবে সংযুক্ত: {info.get('name')} (ID: {info.get('id')})")
        except Exception as e:
            print(f"  ❌ ফেসবুক কানেকশন ত্রুটি: {e}")

    print("\n")

def main():
    parser = argparse.ArgumentParser(description="Autonomous 24/7 Facebook Page Poster")
    parser.add_argument(
        "--slot",
        choices=["morning", "noon", "afternoon", "night", "auto"],
        default="auto",
        help="পোস্টের স্লট নির্বাচন করুন (morning=AI, noon=Tech, afternoon=Cybersecurity, night=Science, auto=সময় অনুযায়ী)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ফেসবুকে পোস্ট না করে শুধুমাত্র লোকাল প্রিভিউ এবং ইমেজ তৈরি করবে"
    )
    parser.add_argument(
        "--skip-image",
        action="store_true",
        help="ইমেজ তৈরি এড়িয়ে শুধু টেক্সট পোস্ট তৈরি করবে"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="API Key ও Facebook Page এক্সেস টোকেনের বৈধতা পরীক্ষা করবে"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="রিসেন্ট পোস্ট গার্ড বাইপাস করে জোরপূর্বক পোস্ট করবে"
    )

    args = parser.parse_args()

    if args.verify:
        verify_credentials()
    else:
        run_poster(slot=args.slot, dry_run=args.dry_run, skip_image=args.skip_image, force=args.force)

if __name__ == "__main__":
    main()
