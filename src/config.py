import os
from datetime import datetime
from pathlib import Path
import pytz
from dotenv import load_dotenv

# Load local .env if available
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_FILE = BASE_DIR / "post_history.json"
TEMP_DIR = BASE_DIR / "temp"

# Ensure temp directory exists
TEMP_DIR.mkdir(exist_ok=True)

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "").strip()
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
FB_APP_ID = os.getenv("FB_APP_ID", "").strip()
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "").strip()
TIMEZONE_NAME = os.getenv("TIMEZONE", "Asia/Dhaka")

# Timezone object
try:
    TZ = pytz.timezone(TIMEZONE_NAME)
except Exception:
    TZ = pytz.timezone("Asia/Dhaka")

# Slot definitions with extensive curated focus areas to prevent repetition
SLOTS = {
    "morning": {
        "name": "সকাল ০৭:০০ (AI)",
        "theme": "Artificial Intelligence (কৃত্রিম বুদ্ধিমত্তা)",
        "description": "এআই নিউজ, নতুন এআই টুলস, জেনারেটিভ এআই, মেশিন লার্নিং, এআই এর বাস্তব প্রভাব ও ভবিষ্যৎ সম্ভাবনা।",
        "focus_areas": [
            "GenAI ও আধুনিক LLM এর নতুন ব্রেকথ্রু এবং প্রয়োগ",
            "দৈনন্দিন জীবনে কাজের গতি ও উৎপাদনশীলতা বাড়ানোর সেরা এআই টুলস",
            "এআই কোডিং অ্যাসিস্ট্যান্ট এবং সফটওয়্যার ডেভেলপমেন্টের ভবিষ্যৎ",
            "ডিপফেক শনাক্তকরণ, এআই এথিক্স ও সাইবার নিরাপত্তা",
            "স্বাস্থ্যসেবা ও জটিল রোগ নির্ণয়ে আর্টিফিশিয়াল ইন্টেলিজেন্সের বিপ্লব",
            "অটোমেটেড হিউম্যানয়েড রোবট ও আধুনিক ফ্যাক্টরি অটোমেশন",
            "অটোনোমাস বা চালকবিহীন গাড়ি ও স্মার্ট ট্রান্সপোর্টেশন",
            "এআই ভয়েস ক্লোনিং, মিউজিক জেনারেশন ও ক্রিয়েটিভ মিডিয়ার ভবিষ্যৎ",
            "শিক্ষা ও গবেষণায় পারসোনালাইজড এআই টিউটরিং প্ল্যাটফর্ম",
            "ফিন্যান্স, শেয়ার মার্কেট ও ব্যাংকিংয়ে এআই অ্যালগরিদম",
            "এআই চিপসেট (Nvidia, TPU, NPU) এবং হার্ডওয়্যার রেভোলিউশন",
            "মাল্টিমোডাল এআই মডেল (টেক্সট, ভিডিও, অডিও ও ইমেজ ইন্টিগ্রেশন)",
            "ব্যবসা ও মার্কেটিং অটোমেশনে ব্যবহৃত কার্যকর এআই স্ট্র্যাটেজি",
            "এআই এজেন্ট এবং স্বয়ংক্রিয় ডিসিশন মেকিং সিস্টেম",
            "এআই এর যুগে তরুণদের জন্য নতুন ক্যারিয়ার ও স্কিলস"
        ],
        "hashtags": ["#ArtificialIntelligence", "#AI", "#TechNews", "#FutureTech", "#বাংলা_টেক", "#BanglaTech"]
    },
    "noon": {
        "name": "দুপুর ১২:০০ (Technology)",
        "theme": "Technology & Innovation (প্রযুক্তি ও আধুনিক উদ্ভাবন)",
        "description": "স্মার্ট গ্যাজেট, কম্পিউটার সায়েন্স, সাইবার নিরাপত্তা, উদ্ভাবনী টেকনোলজি এবং আইটি জ্ঞান।",
        "focus_areas": [
            "নেক্সট-জেন স্মার্টফোন, প্রসেসর ও ৩ ন্যানোমিটার চিপসেট ইনোভেশন",
            "সাইবার সিকিউরিটি, ফিশিং আক্রমণ ও সোশ্যাল মিডিয়া অ্যাকাউন্ট সুরক্ষার উপায়",
            "ক্লাউড কম্পিউটিং ও গ্লোবাল হাইপারস্কেল ডেটা সেন্টারের পরিকাঠামো",
            "ইন্টারনেট অফ থিংস (IoT) ও স্মার্ট হোমের নিত্যনতুন গ্যাজেট",
            "সুপারকম্পিউটার, এক্সাস্কেল কম্পিউটিং ও ভবিষ্যৎ প্রসেসিং ক্ষমতা",
            "স্যাটেলাইট ইন্টারনেট (Starlink) এবং প্রত্যন্ত অঞ্চলে কানেক্টিভিটি",
            "ইলেকট্রিক ভেহিকেল (EV), সলিড স্টেট ব্যাটারি ও দ্রুত চার্জিং প্রযুক্তি",
            "অগমেন্টেড রিয়ালিটি (AR) ও ভার্চুয়াল রিয়ালিটি (VR) হেডসেটের চমক",
            "আধুনিক ওয়াইফাই (Wi-Fi 7), 5G এবং ভবিষ্যৎ 6G নেটওয়ার্ক",
            "স্মার্ট ওয়্যারেবল ও হেলথ ট্র্যাকিং ডিভাইসের সেন্সর প্রযুক্তি",
            "ওপেন সোর্স সফটওয়্যার ও আধুনিক প্রোগ্রামিং দুনিয়ার ট্রেন্ডস",
            "প্রযুক্তি জগতের মজার অজানা ইতিহাস ও সিলিকন ভ্যালির গল্প",
            "সাইবার ক্রাইম রোধে আধুনিক এনক্রিপশন ও বায়োমেট্রিক সিকিউরিটি",
            "স্মার্ট সিটি ও ডিজিটাল গভর্নেন্সের আধুনিক প্রযুক্তি"
        ],
        "hashtags": ["#Technology", "#TechInnovation", "#Gadgets", "#CyberSecurity", "#বাংলা_আইটি", "#TechWorld"]
    },
    "afternoon": {
        "name": "বিকাল ০৪:০০ (Cybersecurity & Smart Tech)",
        "theme": "Cybersecurity & Smart Tech Hacks (সাইবার নিরাপত্তা, প্রাইভেসি ও স্মার্ট টেক ট্রিকস)",
        "description": "অ্যাকাউন্ট নিরাপত্তা, ফিশিং ও সাইবার প্রতারণা থেকে বাঁচার উপায়, ডেটা সুরক্ষা, ক্ষতিকর অ্যাপ শনাক্তকরণ এবং প্রাত্যহিক জীবনের দরকারি ডিজিটাল ট্রিকস।",
        "focus_areas": [
            "সোশ্যাল মিডিয়া ও ফেসবুক অ্যাকাউন্ট হ্যাকিং রোধ এবং টু-ফ্যাক্টর অথেনটিকেশন (2FA) সেটআপ",
            "এআই ডিপফেক ভিডিও ও ভয়েস ক্লোনিং স্ক্যাম শনাক্ত করার সহজ উপায়",
            "পাবলিক ওয়াইফাই (Public Wi-Fi) ব্যবহারের মারাত্মক ঝুঁকি ও নিরাপদে ব্রাউজ করার নিয়ম",
            "ফিশিং লিংক, ওটিপি (OTP) জালিয়াতি ও ভুয়া ব্যাংক মেসেজ চেনার উপায়",
            "স্মার্টফোনের অপ্রয়োজনীয় ক্যাশ ফাইল ও ব্যাকগ্রাউন্ড অ্যাপ বন্ধ করে ফোন ফাস্ট রাখার ট্রিকস",
            "গুগল ও ব্রাউজারে ডিজিটাল ফুটপ্রিন্ট মুছে অনলাইন প্রাইভেসি বজায় রাখার কৌশল",
            "অভেদ্য পাসওয়ার্ড তৈরির কৌশল ও পাসওয়ার্ড ম্যানেজার ব্যবহারের গুরুত্ব",
            "স্মার্টফোনে ক্ষতিকর স্পাইওয়্যার বা ম্যালওয়্যার ঢুকেছে কিনা তা বোঝার লক্ষণ",
            "হোয়াটসঅ্যাপ ও মেসেঞ্জারের জরুরি প্রাইভেসি সেটিংস ও এন্ড-টু-এন্ড এনক্রিপশন",
            "অনলাইন কেনাকাটা ও কার্ড পেমেন্টে ক্লোনিং বা স্ক্যাম থেকে বাঁচার নিয়ম",
            "স্মার্টফোনের ক্যামেরা ও মাইক্রোফোন পারমিশন চেক করে গোপন নজরদারি বন্ধ করা",
            "রিমোট হ্যাকিং এবং সিম সোয়াপিং (SIM Swapping) প্রতারণা থেকে সুরক্ষা",
            "ডিভাইস হারিয়ে বা চুরি হয়ে গেলে দ্রুত ডেটা রিমোট লক ও ডিলিট করার উপায়",
            "ভিপিএন (VPN) আসলে কীভাবে কাজ করে এবং কখন এটি ব্যবহার করা নিরাপদ",
            "শিশুদের জন্য ইন্টারনেট নিরাপদ রাখার প্যারেন্টাল কন্ট্রোল সেটিংস"
        ],
        "hashtags": ["#CyberSecurity", "#OnlineSafety", "#PrivacyTips", "#TechHacks", "#সাইবার_নিরাপত্তা", "#BanglaTech"]
    },
    "night": {
        "name": "রাত ০৮:০০ (Future Tech & Science)",
        "theme": "Future Tech & Breakthrough Innovations (ভবিষ্যৎ প্রযুক্তি, এআই ও আধুনিক বিজ্ঞান)",
        "description": "ফিউচারিস্টিক টেকনোলজি, কোয়ান্টাম কম্পিউটিং, অটোনোমাস রোবোটিক্স, মহাকাশ বিজ্ঞান এবং আধুনিক আবিষ্কার।",
        "focus_areas": [
            "কৃত্রিম বুদ্ধিমত্তা ও নেক্সট-জেন এআই চিপসের বৈপ্লবিক অগ্রগতি",
            "কোয়ান্টাম পদার্থবিজ্ঞান ও কোয়ান্টাম সুপারকম্পিউটিং",
            "জেমস ওয়েব টেলিস্কোপ ও মহাবিশ্বের গভীর মহাজাগতিক রহস্য",
            "অটোনোমাস রোবোটিক্স ও আধুনিক হিউম্যানয়েড বিপ্লব",
            "নিউরোটেকনোলজি ও মানুষের মস্তিষ্কের নিউরাল নেটওয়ার্ক",
            "নবায়নযোগ্য জ্বালানি, নিউক্লিয়ার ফিউশন ও পরিচ্ছন্ন শক্তির ভবিষ্যৎ",
            "মহাকাশ অভিযান এবং সৌরজগতের বাইরে ভবিষ্যৎ বাসস্থানের সন্ধান",
            "জেনেটিক ইঞ্জিনিয়ারিং ও লাইফ-সেভিং আধুনিক বায়োটেক ইনোভেশন",
            "ব্ল্যাকহোল, ইভেন্ট হরাইজন ও মহাকর্ষীয় তরঙ্গের বিজ্ঞান",
            "ভবিষ্যৎ সুপারসনিক ট্রান্সপোর্টেশন ও স্মার্ট এরোস্পেস প্রযুক্তি"
        ],
        "hashtags": ["#FutureTech", "#AI", "#Technology", "#Innovation", "#Science", "#বাংলা_টেক"]
    }
}

def get_current_bst_time():
    """Returns the current datetime in Bangladesh Standard Time."""
    return datetime.now(TZ)

def determine_current_slot() -> str:
    """
    Determines the slot (morning, noon, afternoon, night) based on current hour in Bangladesh.
    - 05:00 - 10:59 => morning (7 AM target)
    - 11:00 - 14:59 => noon (12 PM target)
    - 15:00 - 18:59 => afternoon (4 PM target)
    - 19:00 - 04:59 => night (8 PM target)
    """
    now = get_current_bst_time()
    hour = now.hour

    if 5 <= hour < 11:
        return "morning"
    elif 11 <= hour < 15:
        return "noon"
    elif 15 <= hour < 19:
        return "afternoon"
    else:
        return "night"

SLOT_WINDOWS = {
    "morning": {
        "target_str": "07:00 AM",
        "valid_start": (6, 0),
        "valid_end": (11, 29)
    },
    "noon": {
        "target_str": "12:00 PM",
        "valid_start": (11, 30),
        "valid_end": (15, 29)
    },
    "afternoon": {
        "target_str": "04:00 PM",
        "valid_start": (15, 30),
        "valid_end": (19, 29)
    },
    "night": {
        "target_str": "08:00 PM",
        "valid_start": (19, 30),
        "valid_end": (23, 59)
    }
}

def is_within_slot_window(slot: str, now_dt=None) -> bool:
    """Checks if current time in Bangladesh is within the allowed window for the slot."""
    now = now_dt or get_current_bst_time()
    window = SLOT_WINDOWS.get(slot)
    if not window:
        return True

    current_min = now.hour * 60 + now.minute
    start_min = window["valid_start"][0] * 60 + window["valid_start"][1]
    end_min = window["valid_end"][0] * 60 + window["valid_end"][1]
    return start_min <= current_min <= end_min

