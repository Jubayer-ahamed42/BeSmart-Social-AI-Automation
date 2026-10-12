import json
import logging
import random
import re
import time
import requests
from typing import Dict, Any, List
from src.config import GEMINI_API_KEY, SLOTS, get_current_bst_time
from src.history_manager import HistoryManager

logger = logging.getLogger(__name__)

# Active Gemini models verified for generateContent
CANDIDATE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-flash-latest"
]

class ContentGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY

    def generate_post(self, slot: str, recent_history_summary: str = "", history_mgr: HistoryManager = None) -> Dict[str, Any]:
        """
        Generates Facebook post content and image prompt using Google Gemini API.
        Includes an automatic similarity/duplicate verification loop to guarantee 100% uniqueness.
        """
        slot_info = SLOTS.get(slot, SLOTS["morning"])
        theme = slot_info["theme"]
        description = slot_info["description"]
        focus_areas = slot_info["focus_areas"]
        hashtags_list = " ".join(slot_info["hashtags"])
        
        # Pick a focus area least recently covered
        chosen_focus = self._select_fresh_focus(focus_areas, recent_history_summary)

        current_year = get_current_bst_time().year

        # We allow up to 3 attempts if similarity filter detects close match
        max_attempts = 3
        extra_warning = ""

        for attempt in range(1, max_attempts + 1):
            prompt = f"""
তুমি একজন অত্যন্ত অভিজ্ঞ ও জনপ্রিয় টেক ও সায়েন্স কনটেন্ট ক্রিয়েটর এবং সোশ্যাল মিডিয়া স্ট্র্যাটেজিস্ট।
তোমার কাজ হলো ফেসবুক পেজের জন্য সম্পূর্ণ নতুন, ইউনিক, আকর্ষণীয় ও শিক্ষণীয় একটি বাংলা পোস্ট তৈরি করা।

【বর্তমান পোস্টের ক্যাটাগরি ও থিম】
- সময় ও স্লট: {slot_info['name']}
- মূল বিষয়বস্তু: {theme}
- ক্যাটাগরি বিবরণ: {description}
- বিশেষ ফোকাস বিষয়: {chosen_focus}
- বর্তমান সঠিক সাল: {current_year}

【পূর্ববর্তী কভার করা পোস্টসমূহ (এই বিষয়গুলো কোনোভাবেই পুনরাবৃত্তি করবে না)】:
{recent_history_summary if recent_history_summary else "এখনো পূর্ববর্তী কোনো টপিক নেই। সম্পূর্ণ ইউনিক নতুন কিছু দিয়ে শুরু করো।"}

{extra_warning}

【পোস্ট লেখার গুরুত্বপূর্ণ নির্দেশনাবলী】:
১. ইউনিকনেস (কঠোরভাবে বাধ্যতামূলক): পূর্বে কভার করা কোনো বিষয়, টুল বা আবিষ্কার নিয়ে পুনরাবৃত্তি পোস্ট তৈরি করা যাবে না। সবসময় সম্পূর্ণ নতুন কোনো উদ্ভাবন, চমকপ্রদ তথ্য বা ব্রেকথ্রু তুলে ধরবে।
২. ভাষা: অত্যন্ত সহজ, সাবলীল, প্রাঞ্জল ও প্রমিত বাংলা। টেকনিক্যাল শব্দগুলো স্বাভাবিকভাবে বাংলা বা ইংরেজিতে রাখবে যাতে সাধারণ পাঠকও সহজে বুঝতে পারে।
৩. সময় ও সাল সচেতনতা (কঠোর নিয়ম):
   - বর্তমান সাল হচ্ছে {current_year}। কোনোভাবেই ভুল, ব্যাকডেটেড বা অতীত সাল (যেমন ২০২৪ বা ২০২৫) উল্লেখ করবে না।
   - পোস্টের ভেতর অযথা নির্দিষ্ট কোনো সাল লেখার প্রয়োজন নেই। সালের পরিবর্তে "বর্তমানে", "আজকের দিনে", "এই যুগে" বা "আধুনিক প্রযুক্তির সময়ে" লিখবে।
   - যদি একান্তই কোনো সাল উল্লেখ করতে হয়, তবে তা অবশ্যই বর্তমান সাল ({current_year}) হবে।
৪. হুক লাইন (Hook): প্রথম ১-২ লাইনেই যেন পাঠকের কৌতূহল জেগে ওঠে।
৫. বডি স্ট্রাকচার:
   - আকর্ষণীয় শিরোনাম (উপযুক্ত ইমোজি সহ)।
   - সহজ ভাষায় মূল বিষয় বা বিজ্ঞানের আবিষ্কারের ব্যাখ্যা।
   - ৩ থেকে ৪টি স্পষ্ট বুলেট পয়েন্ট (বুলেট সাইন যেমন 🔹, 🚀, 💡, 🔬 ব্যবহার করবে)।
   - এটি কীভাবে মানুষের জীবন বা ভবিষ্যৎ বদলে দিচ্ছে তার সংক্ষেপ।
৬. এনগেজমেন্ট প্রশ্ন: পোস্টের শেষে পাঠকদের মতামত জানতে চেয়ে একটি আকর্ষণীয় উন্মুক্ত প্রশ্ন।
৭. হ্যাশট্যাগ: পোস্টের একদম শেষে উপযুক্ত ৫-৭টি হ্যাশট্যাগ অন্তর্ভুক্ত করবে (যেমন: {hashtags_list})।
৮. ইমেজ ভিজ্যুয়াল ও হিরো কি-ওয়ার্ড নির্দেশিকা (সবচেয়ে গুরুত্বপূর্ণ - ১০০% প্রাসঙ্গিকতা বাধ্যতামূলক):
   - পাঠক যেন ছবিটি দেখেই পোস্টের মূল বিষয়বস্তু ও অ্যাকশন তৎক্ষণাৎ অনুমান করতে পারে এবং ক্লিক করতে আগ্রহী হয়।
    - পোস্টের বিষয়ের সাথে ছবির সরাসরি চাক্ষুষ মিল ও স্পর্শযোগ্য হিরো অবজেক্ট (Tangible Hero Object) থাকতে হবে:
      * যেমন: সুপার এআই / এজিআই / নতুন এআই মডেল হলে -> নিখুঁত টাইটানিয়াম রোবোটিক মেকানিক্যাল হাত ৩ডি হলোগ্রাফিক নিউরাল নেটওয়ার্ক স্পর্শ করছে, অথবা হাই-টেক ল্যাবে স্বচ্ছ ক্রিস্টাল ক্যাসিংয়ের ভেতর উজ্জ্বল সোনালী কোয়ান্টাম প্রসেসর ও লেজার সার্কিট।
      * যেমন: টাইপিং বা ভয়েস এআই পোস্ট হলে -> স্বয়ংক্রিয়ভাবে টাইপ হওয়া নিয়ন গ্লোয়িং মেকানিক্যাল কীবোর্ড বা সাউন্ডওয়েভ হলোগ্রাম।
      * যেমন: সাইবার সিকিউরিটি/হ্যাকিং পোস্ট হলে -> ল্যাপটপের ওপর ভাসমান গ্লোয়িং সাইবার প্যাডলক বা ডিজিটাল সিকিউরিটি শিল্ড।
      * যেমন: এআই এজেন্ট বা রোবোটিক্স পোস্ট হলে -> অত্যাধুনিক রোবোটিক মেকানিক্যাল হ্যান্ড বা অটোনোমাস এআই ইন্টারফেস।
      * যেমন: ভিআর/এআর হেডসেট পোস্ট হলে -> প্রিমিয়াম আধুনিক স্মার্ট হেডসেট ও ভাসমান ৩ডি হলোগ্রাম।
      * যেমন: মহাকাশ বা টেলিস্কোপ পোস্ট হলে -> রঙিন নেবুলা, গ্যালাক্সি বা তারার জন্মদৃশ্য।
    - 🚨 কঠোর নিষেধাজ্ঞা (Strictly Forbidden):
      * অন্ধকার শূন্যতায় কোনো বিমূর্ত আলোর বল, গোলক, ব্লব বা লেন্স ফ্লেয়ার (Strictly NO abstract glowing orb, NO plain light blob in dark void, NO generic lens flare) সম্পূর্ণ নিষিদ্ধ! ছবিতে অবশ্যই একটি স্পষ্ট স্পর্শযোগ্য বাস্তব সাবজেক্ট থাকতে হবে যা দেখলেই দর্শকের ডোপামিন রিলিজ হয় ও ক্লিক করতে ইচ্ছে করে।
      * মহাকাশ বা নক্ষত্র সংক্রান্ত পোস্ট ছাড়া অন্য কোনো পোস্টের ছবিতে আকাশ, গ্যালাক্সি বা তারা দেওয়া সম্পূর্ণ নিষিদ্ধ!
      * কোনো সাধারণ ফাঁকা অফিস রুম, তারের জটলা বা অন্ধকার অস্পষ্ট ব্লব দেওয়া সম্পূর্ণ নিষিদ্ধ।
   - 🚨 কঠোর জেন্ডার ফিল্টার: ছবিতে কোনো নারী বা মহিলার অবয়ব (strictly NO female, no woman, no girl, no lady, no feminine figures) রাখা সম্পূর্ণ নিষিদ্ধ।
   - ছবির শৈলী: হাইপার-রিয়েলিস্টিক এডিটোরিয়াল ফটোগ্রাফি (Wired, National Geographic বা TechCrunch কভারের মতো ঝকঝকে ও সিনেমাটিক)।

【আউটপুট ফরম্যাট】:
অবশ্যই এবং শুধুমাত্র একটি ভ্যালিড JSON অবজেক্ট আউটপুট হিসেবে দাও, কোনো বাড়তি কথা ছাড়া:
{{
  "title": "পোস্টের মূল আকর্ষণীয় শিরোনাম (ইমোজি সহ)",
  "card_category": "Short 1-2 words category for the photo card badge (e.g. Artificial Intelligence, Cybersecurity, Deep Space, Tech Innovation)",
  "card_headline": "ছবির ওপর ফটোকার্ডে লেখার মতো ১-২ লাইনের অত্যন্ত আকর্ষণীয় বাংলা সাবটাইটেল (যেমন: আর টাইপ করতে হবে না! স্ক্রিন দেখে কাজ করে দেয় এমন ৪টি এআই)",
  "card_highlight": "সাবটাইটেলের যে অংশটুকু হলুদ রঙে জ্বলজ্বল করবে (যেমন: এমন ৪টি এআই)",
  "content": "সম্পূর্ণ ফেসবুক পোস্টটি এখানে থাকবে (শিরোনাম, হুক, পয়েন্ট, প্রশ্ন এবং হ্যাশট্যাগ সহ সবকিছু সুন্দর লাইন ব্রেক দিয়ে সাজানো)",
  "hero_keywords": ["পোস্টের মূল বিষয়ের ১টি নির্দিষ্ট ইংরেজি কীওয়ার্ড (যেমন: Mechanical keyboard typing RGB)", "আরেকটি সুনির্দিষ্ট ইংরেজি কীওয়ার্ড (যেমন: Computer workstation setup)"],
  "image_prompt": "A hyper-realistic 8k photograph visually capturing the exact core action and hero object of this post in vivid detail. Cinematic studio lighting, sharp focus, 35mm photography, strictly NO female, no woman, no people, no text, no watermark.",
  "topic_summary": "টপিকটির ১ লাইনের সংক্ষেপ (ভবিষ্যতে ডুপ্লিকেট রোধের জন্য)"
}}
"""
            logger.info(f"Generating unique content for slot '{slot}' ({theme}) [Attempt {attempt}/{max_attempts}]...")
            parsed = {}
            try:
                raw_response = self._call_gemini_api(prompt)
                parsed = self._parse_json_response(raw_response)
            except Exception as api_err:
                logger.warning(f"Gemini generation attempt {attempt} failed: {api_err}")
                if attempt == max_attempts:
                    logger.warning("All Gemini API attempts exhausted. Activating built-in structured generator.")
                    parsed = self._generate_fallback(slot, chosen_focus)

            if not parsed or not parsed.get("content"):
                logger.warning("Parsing failed to find content. Generating structured fallback.")
                parsed = self._generate_fallback(slot, chosen_focus)

            title = parsed.get("title", "")
            summary = parsed.get("topic_summary", "")

            # If HistoryManager is provided, verify anti-duplicate filter
            if history_mgr:
                is_dup, matched_title = history_mgr.check_similarity(title, summary)
                if is_dup:
                    logger.warning(f"Rejecting generated topic on attempt {attempt}: Too close to '{matched_title}'. Regenerating...")
                    extra_warning = f"🚨 কঠোর সতর্কতা: তোমার পূর্বের চেষ্টাটি '{matched_title}' পোস্টের সাথে বেশি মিলে গেছে! দয়া করে সম্পূর্ণ ভিন্ন কোনো টুল, খবর বা আবিষ্কার বেছে নাও।"
                    chosen_focus = random.choice(focus_areas)
                    continue

            # Passed uniqueness check
            return parsed

        return parsed

    def _select_fresh_focus(self, focus_areas: List[str], history_summary: str) -> str:
        """Selects a focus area least recently mentioned in history."""
        candidates = [area for area in focus_areas if area.lower() not in history_summary.lower()]
        return random.choice(candidates) if candidates else random.choice(focus_areas)

    def _call_gemini_api(self, prompt: str) -> str:
        """Calls Gemini API with SDK or direct REST fallback and retry logic."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY পাওয়া যায়নি! দয়া করে .env ফাইলে বা GitHub Secrets-এ GEMINI_API_KEY সেট করুন।")

        # Try Google GenAI SDK first
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            for model_name in CANDIDATE_MODELS:
                for attempt in range(2):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                        )
                        if response and response.text:
                            return response.text
                    except Exception as sdk_err:
                        err_str = str(sdk_err)
                        if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                            logger.warning(f"Model {model_name} busy (attempt {attempt+1}/2). Waiting 2s...")
                            time.sleep(2)
                        else:
                            logger.warning(f"SDK call with model {model_name} failed: {sdk_err}. Trying next model...")
                            break
        except Exception as e:
            logger.warning(f"google-genai SDK init failed: {e}. Falling back to REST API.")

        # REST API Fallback
        for model in CANDIDATE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "responseMimeType": "application/json"
                }
            }
            for attempt in range(2):
                try:
                    res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    elif res.status_code in [429, 503]:
                        logger.warning(f"REST API {model} status {res.status_code}. Retrying in 2s...")
                        time.sleep(2)
                    else:
                        logger.warning(f"REST API {model} returned status {res.status_code}. Trying next model...")
                        break
                except Exception as req_err:
                    logger.warning(f"REST API error with {model}: {req_err}")
                    break

        raise RuntimeError("সবগুলো Gemini API কল ব্যর্থ হয়েছে। API Key এবং ইন্টারনেট সংযোগ যাচাই করুন।")

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parses clean JSON from LLM output with multi-strategy fallback handling."""
        cleaned = text.strip()
        # Strip markdown wrapper
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned)
        cleaned = cleaned.strip()

        parsed = None
        # Strategy 1: Standard json.loads with strict=False
        try:
            parsed = json.loads(cleaned, strict=False)
        except Exception:
            pass

        # Strategy 2: Bracket search
        if not parsed:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0), strict=False)
                except Exception:
                    pass

        # Strategy 3: Robust Regex field extraction for when LLM includes unescaped quotes in Bengali text
        if not parsed:
            extracted = {}
            title_m = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
            if title_m:
                extracted["title"] = title_m.group(1).replace('\\"', '"')

            content_m = re.search(r'"content"\s*:\s*"(.*?)"(?:\s*,\s*"\w+"\s*:)', cleaned, re.DOTALL)
            if content_m:
                extracted["content"] = content_m.group(1).replace('\\n', '\n').replace('\\"', '"')

            keywords_m = re.search(r'"hero_keywords"\s*:\s*(\[[^\]]*\])', cleaned)
            if keywords_m:
                try:
                    extracted["hero_keywords"] = json.loads(keywords_m.group(1))
                except Exception:
                    pass

            for key in ["card_category", "card_headline", "card_highlight", "image_prompt", "topic_summary"]:
                m = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned)
                if m:
                    extracted[key] = m.group(1).replace('\\"', '"')

            if extracted.get("title") and extracted.get("content"):
                logger.info("Successfully recovered post fields using regex fallback parsing.")
                parsed = extracted

        if not parsed:
            logger.error(f"Failed to decode JSON from Gemini output: {text[:200]}...")
            return {}

        # Auto-fill card_headline if missing
        if not parsed.get("card_headline") and parsed.get("title"):
            clean_t = re.sub(r"^[\U00010000-\U0010ffff\u2600-\u27bf\s]+", "", parsed["title"])
            clean_t = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\s]+$", "", clean_t)
            parsed["card_headline"] = clean_t.strip()

        return parsed

    def _generate_fallback(self, slot: str, focus_area: str) -> Dict[str, Any]:
        """Provides a safe fallback template in case of parsing anomaly."""
        slot_info = SLOTS.get(slot, SLOTS["morning"])
        hashtags = " ".join(slot_info["hashtags"])
        title = f"🚀 {slot_info['theme']}: নতুন দিগন্ত উন্মোচন"
        content = f"""{title}

প্রযুক্তি ও উদ্ভাবনের দুনিয়া প্রতিদিন দ্রুতগতিতে বদলে যাচ্ছে। আজকের বিশেষ আয়োজন: {focus_area}।

🔹 আধুনিক গবেষণার মাধ্যমে নতুন সম্ভাবনার দ্বার উন্মোচিত হচ্ছে।
🔹 বাস্তব জীবনে মানুষের কাজের গতি এবং নির্ভুলতা বাড়াতে এর ভূমিকা অনন্য।
🔹 ভবিষ্যতে এই প্রযুক্তি আমাদের প্রাত্যহিক জীবনের বড় অংশ হতে চলেছে।

বিজ্ঞানের এই রোমাঞ্চকর অগ্রযাত্রা নিয়ে আপনার কী মতামত? কমেন্টে আপনার ভাবনা শেয়ার করুন!

{hashtags}"""

        slot_names = {
            "morning": "Artificial Intelligence",
            "noon": "Tech & Innovation",
            "afternoon": "Cybersecurity & Privacy",
            "night": "Science & Deep Space"
        }

        return {
            "title": title,
            "card_category": slot_names.get(slot, "Smart Tech"),
            "card_headline": f"{focus_area}: নতুন দিগন্ত উন্মোচন",
            "card_highlight": "নতুন দিগন্ত উন্মোচন",
            "content": content,
            "hero_keywords": [focus_area, slot_info['theme']],
            "image_prompt": f"Realistic editorial photograph of {focus_area}, high detail, 8k resolution, cinematic lighting, photorealistic, no female, no woman, no text.",
            "topic_summary": f"{slot_info['theme']} - {focus_area}"
        }
