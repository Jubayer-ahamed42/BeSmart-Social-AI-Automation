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
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "8801610594042").strip()

# Timezone object
try:
    TZ = pytz.timezone(TIMEZONE_NAME)
except Exception:
    TZ = pytz.timezone("Asia/Dhaka")

# Dual-Slot 24/7 Automation Configuration:
# 1. noon (12:00 PM BST): Everyday People (Students, Job-holders, Freelancers) - Practical AI Hacks & Productivity
# 2. night (08:00 PM BST): Business Owners, Founders & Co-Founders - B2B AI Automation & Inbound Client Acquisition
SLOTS = {
    "noon": {
        "name": "দুপুর ১২:০০ (AI Productivity & Life Hacks)",
        "target_time": "12:00 PM BST",
        "theme": "AI Productivity & Real-Life Automation (দৈনন্দিন এআই অটোমেশন ও প্রোডাক্টিভিটি)",
        "description": "ছাত্রছাত্রী, চাকরিজীবী, ফ্রিল্যান্সার ও সাধারণ মানুষের জন্য বাস্তব জীবনে কাজে লাগার মতো এআই ট্রিকস, এক্সেল অটোমেশন, ফ্রি এআই টুলস, ক্যারিয়ার স্কিলস ও সময় বাঁচানোর উপায়।",
        "focus_areas": [
            "Excel ও স্প্রেডশীটে ঘণ্টার পর ঘণ্টা কাজ ১টি কাস্টম প্রম্পটে অটোমেশন",
            "Google NotebookLM দিয়ে ১০০ পাতার বই বা রিসার্চ পেপারের ৫ মিনিটে নির্ভুল সামারি",
            "ChatGPT Voice দিয়ে ঘরে বসে ফ্রিতে Spoken English ও IELTS Speaking মক টেস্ট",
            "যেকোনো চাকরির সার্কুলার অনুযায়ী ২ মিনিটে ATS-ফ্রেন্ডলি সিভি (CV) কাস্টমাইজেশন",
            "Upwork ও Fiverr-এ জেনেরিক কপি-পেস্ট বাদ দিয়ে ক্লায়েন্ট উইনিং প্রপোজাল তৈরির মেথড",
            "ক্যানভা ও এআই দিয়ে সোশ্যাল মিডিয়া পোস্ট ডিজাইন ও বাল্ক কনটেন্ট জেনারেশন",
            "কোডিং না জেনেও v0.dev ও Bolt.new দিয়ে পার্সোনাল ওয়েবসাইট বা ওয়েব টুল বিল্ডিং",
            "রবিবারের ১৫ মিনিটের এআই টাইম-ব্লকিং: সারা সপ্তাহের কাজের প্রায়োরিটি শিডিউলিং",
            "অফিসের বোরিং ও জটিল ইমেইলের পোলাইট ও প্রফেশনাল রিপ্লাই ড্রাফটিং",
            "বড় মিটিং ও জুম কলের রেকর্ডিং থেকে অটোমেটিক মিনিট্স ও অ্যাকশন আইটেম বের করা",
            "ফটোশপ ছাড়াই মোবাইলে তোলা সাধারণ ছবির ব্যাকগ্রাউন্ড ও কোয়ালিটি এনহ্যান্সমেন্ট",
            "জটিল প্রেজেন্টেশন স্লাইড ২ মিনিটে তৈরি করার আধুনিক এআই প্রেজেন্টেশন টুলস",
            "মাসে ২০ ডলার খরচ না করে ChatGPT Plus ও Midjourney-এর সেরা ফ্রি বিকল্পসমূহ",
            "গুগল ড্রাইভ ও জিমেইলে জমে থাকা হাজারো ফাইল ও মেইল দ্রুত অর্গানাইজ করার ট্রিকস",
            "অ্যাসাইনমেন্ট ও থিসিস পেপারে ফেক সাইটেশন এড়ানোর বিশ্বস্ত এআই রিসার্চ টেকনিক",
            "চাকরির ইন্টারভিউতে বসের কঠিন প্রশ্নের উত্তর প্র্যাকটিসের ইন্টারভিউয়ার প্রম্পট",
            "মোবাইল দিয়ে ডকুমেন্টের ছবি তুলে ইনস্ট্যান্ট এডিটেবল ওয়ার্ড ফাইলে রূপান্তর",
            "ইংরেজি ইমেইল ও আর্টিকেলের গ্রামার ও টোন মানুষের মতো ন্যাচারাল করার উপায়",
            "দৈনন্দিন পার্সোনাল বাজেট ও খরচ ট্র্যাকিং সহজ করার স্মার্ট এআই শিট",
            "ইউটিউব বা পডকাস্টের ১ ঘণ্টার দীর্ঘ আলোচনা ৫ মিনিটে বাংলায় বোঝার উপায়",
            "প্রোগ্রামিং শেখার শুরুতে জটিল কোডের সহজ বাংলা ব্যাখ্যা পাওয়ার প্রম্পট",
            "বই পড়ার সময় না থাকলে যেকোনো নন-ফিকশন বইয়ের মূল শিক্ষা ১০ মিনিটে নেওয়া",
            "স্মার্টফোনে ক্যাশ ক্লিন ও ব্যাটারি ড্রেন রোধ করে ফোন ফাস্ট রাখার ডিজিটাল হাইজিন",
            "অনলাইন স্ক্যাম ও ভুয়া ফিশিং লিংক চেনার সবচেয়ে সহজ সাধারণ টেকনিক",
        ],
        "hashtags": ["#BeSmartWithAI", "#AIProductivity"]
    },
    "night": {
        "name": "রাত ০৮:০০ (B2B Business Automation)",
        "target_time": "08:00 PM BST",
        "theme": "B2B Business Process Automation & Growth (ব্যবসায়িক অটোমেশন ও গ্রোথ)",
        "description": "ব্যবসায়ী, ই-কমার্স ওনার, এজেন্সি ও কো-ফাউন্ডারদের জন্য এআই অটোমেশন—রাত ২টার সেলস মিস বন্ধ করা, ২৪/৭ স্মার্ট সেলস বট, কুরিয়ার অটোমেশন (Steadfast/Pathao), সিওডি কনফার্মেশন ও রিটার্ন কমানো, ব্যাক-অফিস খরচ ৭০% কমানো, কোল্ড লিড ফলো-আপ এবং এআই সিস্টেমস আর্কিটেকচার।",
        "focus_areas": [
            "রাত ১১টা থেকে ভোর ৩টার ইনবক্স সেলস মিস বন্ধ করার 24/7 AI Sales Agent",
            "জিরো-ক্লিক কুরিয়ার অটোমেশন: মেসেঞ্জার অর্ডার থেকে অটোমেটিক Steadfast/Pathao কনসাইনমেন্ট জেনারেশন",
            "২৫% ক্যাশ-অন-ডেলিভারি (COD) রিটার্ন কমাতে ৬০ সেকেন্ডের অটোমেটিক WhatsApp ভেরিফিকেশন",
            "ইনবক্সে সারাদিন 'দাম কত' জ্যাম বাদ দিয়ে রিয়েল বায়ারদের মিটিং ক্যালেন্ডারে বুক করার লিড ফিল্টারিং",
            "৩ জন সাপোর্ট স্টাফের কাজ ১টি সিস্টেমে: কাস্টমার সাপোর্ট খরচ ৭০% কমানোর উপায়",
            "৮০% বায়ার 'পরে জানাচ্ছি' বলে হারিয়ে যায়: কোল্ড লিড রিকভারি ফলো-আপ ইঞ্জিন",
            "ম্যানুয়াল ডেটা এন্ট্রি বাদ দিয়ে ইনভয়েস ও ভেন্ডর পেমেন্ট রিকনসিলিয়েশন অটোমেশন",
            "কোম্পানির সমস্ত SOP ও পলিসি দিয়ে প্রাইভেট AI Business OS ও স্টাফ অনবোর্ডিং",
            "ফেসবুক অ্যাডের কস্ট পার মেসেজ (CPL) কমাতে ২০টি AI অ্যাড ক্রিয়েটিভ ভ্যারিয়েশন টেস্টিং",
            "রিয়েল এস্টেট ও কনসালটেন্সির ভিআইপি লিডকে ৫ মিনিটের মধ্যে হোয়াটসঅ্যাপে কনভার্ট করার পাইপলাইন",
            "নতুন ৫ জন স্টাফ হায়ার না করে ৫০ অর্ডার থেকে ৫০০ অর্ডারে ব্যবসা স্কেল করার ব্লুপ্রিন্ট",
            "গুগল শিট থেকে অটোমেটিক WhatsApp ইনভয়েস ও পেমেন্ট রিমাইন্ডার পাঠানোর সিস্টেম",
            "কাস্টমার চ্যাটে সাইজ ও কালার স্টকের রিয়েল-টাইম ডেটাবেজ চেক ও ইনস্ট্যান্ট অর্ডার ক্লোজিং",
            "একই কাস্টমারকে দ্বিতীয়বার কেনাতে অটোমেটেড পোস্ট-পারচেজ লয়্যালটি সিকোয়েন্স",
            "এজেন্সির ক্লায়েন্ট রিপোর্টিং ও সোশ্যাল অ্যানালিটিক্স রিপোর্ট অটো-জেনারেট করা",
            "অর্ডারের ফোন নম্বর ও ঠিকানা ভুল হওয়া ঠেকাতে স্মার্ট অ্যাড্রেস ভ্যালিডেশন বট",
            "মাল্টি-চ্যানেল চ্যাট (Facebook, Instagram, WhatsApp) এক স্ক্রিনে সেন্ট্রালাইজড এআই সাপোর্ট",
            "সেলস টিমের পারফরম্যান্স ও কনভার্সন রেট স্বয়ংক্রিয়ভাবে ট্র্যাক করার স্মার্ট ড্যাশবোর্ড",
            "কোম্পানি ফাউন্ডার ছুটিতে গেলেও ব্যবসা অটোমেটিক চলার আনইন্টারাপ্টেড সিস্টেম আর্কিটেকচার",
            "অ্যাডের লিড ফর্ম ফিলাপ করার ৯০ সেকেন্ডে অটো-কল বা হোয়াটসঅ্যাপ ভয়েস নোট ডেলিভারি",
            "রিটার্ন পার্সেলের কুরিয়ার লস কমাতে হাই-রিস্ক ফেক অর্ডার আইডেন্টিফিকেশন সিস্টেম",
            "ভেন্ডর বিল ও মেমো ছবি তুলে পাঠালেই অটোমেটিক গুগল শিটে লেজার তৈরি",
            "ফেসবুক পেজের কমেন্টে যারা দাম জানতে চায় তাদের ইনস্ট্যান্ট অটোমেটিক ইনবক্স মেসেজিং",
            "কাস্টমার রিভিউ ও কমপ্লেন এনালাইসিস করে প্রোডাক্টের কোয়ালিটি ইস্যু দ্রুত শনাক্তকরণ",
        ],
        "hashtags": ["#BeSmartWithAI", "#BusinessAutomation"]
    }
}

def get_current_bst_time():
    """Returns the current datetime in Bangladesh Standard Time."""
    return datetime.now(TZ)

def determine_current_slot() -> str:
    """
    Determines the slot (noon, night) based on current hour in Bangladesh.
    - 05:00 - 15:59 => noon (12:00 PM target)
    - 16:00 - 04:59 => night (08:00 PM target)
    """
    now = get_current_bst_time()
    hour = now.hour

    if 5 <= hour < 16:
        return "noon"
    else:
        return "night"

SLOT_WINDOWS = {
    "noon": {
        "target_str": "12:00 PM",
        "valid_start": (11, 0),
        "valid_end": (16, 59)
    },
    "night": {
        "target_str": "08:00 PM",
        "valid_start": (19, 0),
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
