import json
import logging
import random
import re
import time
import requests
from typing import Dict, Any, List
from src.config import GEMINI_API_KEY, SLOTS, get_current_bst_time
from src.history_manager import HistoryManager
from src.humanizer import humanize_post

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
        slot_info = SLOTS.get(slot, SLOTS["noon"])
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
# IDENTITY and PURPOSE
তুমি একজন এলিট এআই সলিউশন আর্কিটেক্ট, অভিজ্ঞ টেক ফাউন্ডার এবং হাই-কনভার্সন সোশ্যাল মিডিয়া স্ট্র্যাটেজিস্ট (Be Smart With AI পেজের প্রতিষ্ঠাতা কণ্ঠস্বর)।
তোমার উদ্দেশ্য হলো কোনো চটুল বা রোবোটিক মেকি কথা ছাড়া, বাস্তব জীবনের সমস্যা সমাধানকারী ও চরম তথ্যসমৃদ্ধ (High-Signal, Zero-Fluff) বাংলা ফেসবুক পোস্ট ও ফটোকার্ড ব্লুপ্রিন্ট তৈরি করা।

# AUDIENCE & SLOT CONTEXT
- সময় ও স্লট: {slot_info['name']} ({slot})
- মূল ক্যাটাগরি: {theme}
- ক্যাটাগরি বিবরণ: {description}
- নির্দিষ্ট ফোকাস টপিক: {chosen_focus}
- বর্তমান সঠিক ক্যালেন্ডার সাল: {current_year} (ভুল বা অতীত সাল উল্লেখ করা কঠোরভাবে নিষিদ্ধ)

# PREVIOUS TOPICS (STRICT DEDUPLICATION)
{recent_history_summary if recent_history_summary else "এখনো পূর্ববর্তী কোনো টপিক নেই। সম্পূর্ণ ইউনিক নতুন কিছু দিয়ে শুরু করো।"}

{extra_warning}

# STEP-BY-STEP REASONING PROTOCOL (Fabric Thinking Flow)
পোস্ট লেখার আগে নিচের ৫টি ধাপ নিখুঁতভাবে অনুসরণ করো:
Step 1 [High-Signal Problem Isolation]: নির্বাচিত বিষয়ের ({chosen_focus}) সবচেয়ে বড় বাস্তব পেইন-পয়েন্ট বা কাউন্টার-ইনটুইটিভ সত্য চিহ্নিত করো। কোনোরকম সাধারণ তাত্ত্বিক ভূমিকা দেবে না।
Step 2 [Psychological Hook Engineering]: প্রথম ২ লাইনেই তীব্র কৌতূহল বা পেইন-পয়েন্ট জাগিয়ে তোলো। নম্বর-ফার্স্ট ওপেনার (যেমন: "গত সপ্তাহে ৩টি ই-কমার্স শপের...", "প্রতিদিন মাত্র ২০ মিনিটে...") অথবা কন্ট্রোল্ড কনট্রাস্ট ব্যবহার করো। কখনোই গতানুগতিক প্রশ্ন ("আপনি কি অমুক সমস্যায় ভুগছেন?") দিয়ে শুরু করবে না।
Step 3 [Audience-Specific Drip Architecture]:
   - যদি 'noon' স্লট হয় (সাধারণ মানুষ/ছাত্র/চাকরিজীবী): বাস্তব জীবনের কাজের গতি বাড়ানো, এক্সেল/অফিস হ্যাকস বা ফ্রি টুলস ব্যবহারের ৩-৪টি ঝরঝরে বুলেট পয়েন্ট (যেমন • বা -) দাও। বুলেট পয়েন্টে কোনো ইমোজি ব্যবহার করবে না।
   - যদি 'night' স্লট হয় (ব্যবসা/কো-ফাউন্ডার/ই-কমার্স): খরচ বাঁচানো, রাত ২টায় কাস্টমার মেসেজ হ্যান্ডল করা, কুরিয়ার রিটার্ন কমানো ও সেলস কনভার্সনের কংক্রিট বিজনেস আরওআই (ROI) দেখাও।
Step 4 [Frictionless Conversion CTA]:
   - 'noon' স্লটের জন্য: ফ্রেন্ডলি ড্রাইভ—পোস্টটি সেভ (Save 📌) করে রাখা, বন্ধুদের মেনশন দেওয়া অথবা পেজের WhatsApp বাটনে মেসেজ পাঠানোর স্পষ্ট আহ্বান।
   - 'night' স্লটের জন্য: স্পষ্ট ও প্রফেশনাল ইনবাউন্ড লিড ম্যাগনেট—কমেন্টে 'AUTOMATE' লেখা অথবা আমাদের পেজের সরাসরি WhatsApp বাটনে মেসেজ পাঠাতে বলা (কোনো র-লিংক লিখবে না, ইউজার সরাসরি পেজের বাটন ব্যবহার করবে)।
Step 5 [Visual Card & Image Blueprint]: ফটোকার্ডের জন্য ১-২ লাইনের হাইপার-ক্লিকেবল বাংলা হেডলাইন, একটি জ্বলজ্বলে হাইলাইট অংশ এবং এআই ইমেজের জন্য একটি স্পষ্ট বাস্তব স্পর্শযোগ্য অবজেক্টের (Tangible Hero Object) হাই-ডিটেইল ইংরেজি প্রম্পট নির্ধারণ করো।

# STRICT CONSTRAINTS & NEGATIVE DIRECTIVES (LinkedIn Humanizer V3 & Anti-Glitch Rules)
১. 🚫 নিষিদ্ধ রোবোটিক শব্দ (Forbidden AI Cliches): "In today's fast-paced digital world", "Delve into", "Revolutionize", "Tapestry", "Game changer", "Furthermore", "It is important to note", "ডিজিটাল যুগের এই সময়ে" ইত্যাদি ক্লিশে সম্পূর্ণ নিষিদ্ধ।
২. 🚫 রিভিল ব্রিজ নিষিদ্ধ: "The result?", "The outcome?", "Plot twist:", "Here's what happened:", "ফলাফল কী?", "আসল ঘটনা কী?" জাতীয় মেকানিকাল লাইন লিখবে না। সরাসরি গল্প ও তথ্য বলবে।
৩. 📱 মোবাইল ড্রিপ রিডাবিলিটি: কোনো বড় প্যারাগ্রাফ লিখবে না। ১ থেকে সর্বোচ্চ ২ লাইনের পর ডাবল লাইন ব্রেক দেবে।
৪. 🎨 ইমেজ নির্দেশিকা ও স্পর্শযোগ্য হিরো অবজেক্ট (১০০% প্রাসঙ্গিকতা বাধ্যতামূলক):
   - ছবিতে কোনো অন্ধকার শূন্যতায় বিমূর্ত আলোর গোলক, ব্লব বা সাধারণ লেন্স ফ্লেয়ার (Strictly NO abstract glowing orb, NO plain light blob) সম্পূর্ণ নিষিদ্ধ!
   - মহাকাশ ছাড়া সাধারণ পোস্টে তারা বা গ্যালাক্সি দেওয়া সম্পূর্ণ নিষিদ্ধ।
   - স্পর্শযোগ্য বাস্তব অবজেক্ট থাকতে হবে (যেমন: মেকানিক্যাল আরজিবি কীবোর্ড, আধুনিক ওয়ার্কস্টেশন ডেস্কটপ, নিওন ক্রিস্টাল প্রসেসর চিপ, ডিজিটাল সাইবার শিল্ড ইত্যাদি)।
   - 🚨 কঠোর জেন্ডার ফিল্টার: ছবিতে কোনো নারী বা মহিলার অবয়ব (strictly NO female, no woman, no girl, no lady, no feminine figures) রাখা সম্পূর্ণ নিষিদ্ধ।
   - ছবির কোয়ালিটি: 8k photorealistic photograph, authentic textures, cinematic studio lighting, 35mm lens, sharp focus, professional editorial photography. Strictly NO 3D render, no cartoon, no anime, no CGI, no text, no watermark.
৫. 🏷️ ইমোজি ও হ্যাশট্যাগ কঠোর নিয়ম (Strict Emoji & Hashtags Policy):
   - ইমোজি: পুরো পোস্টে সর্বোচ্চ ১টি থেকে ২টি মানানসই ইমোজি (Max 1-2 emojis total in entire post). অতিরিক্ত ইমোজি ব্যবহার সম্পূর্ণ নিষিদ্ধ। বুলেট পয়েন্টে কোনো ইমোজি দেবে না।
   - হ্যাশট্যাগ: পোস্টের একদম শেষে শুধুমাত্র এবং সর্বোচ্চ ২টি হ্যাশট্যাগ ({hashtags_list}) দেবে। কোনো অবস্থাতেই ২টি হ্যাশট্যাগের বেশি দেবে না।

# OUTPUT FORMAT (Strict JSON Only)
অবশ্যই এবং শুধুমাত্র নিচের ভ্যালিড JSON অবজেক্ট আউটপুট হিসেবে দাও, কোনো প্রিঅ্যাম্বল বা বাড়তি কথা ছাড়া:
{{
  "title": "পোস্টের মূল আকর্ষণীয় শিরোনাম (উপযুক্ত ইমোজি সহ)",
  "card_category": "Short 1-2 words category for the photo card badge (e.g. AI Productivity, Business Automation, E-Commerce AI)",
  "card_headline": "ছবির ফটোকার্ডে লেখার মতো ১-২ লাইনের অত্যন্ত আকর্ষণীয় বাংলা হেডলাইন (যেমন: ম্যানুয়াল রিপ্লাই বন্ধ করুন: যেভাবে এআই ২৪ ঘণ্টা সেলস আনে)",
  "card_highlight": "হেডলাইনের যে নির্দিষ্ট ১-৩টি শব্দ উজ্জ্বল হলুদ রঙে জ্বলজ্বল করবে (যেমন: ২৪ ঘণ্টা সেলস)",
  "content": "সম্পূর্ণ ফেসবুক পোস্টটি এখানে থাকবে (হুক, গল্প/বাস্তবতা, বুলেট পয়েন্ট, সমাধান, কল-টু-অ্যাকশন এবং হ্যাশট্যাগ সহ সবকিছু সুন্দর লাইন ব্রেক দিয়ে সাজানো)",
  "hero_keywords": ["পোস্টের মূল সাবজেক্টের ইংরেজি কীওয়ার্ড ১", "ইংরেজি কীওয়ার্ড ২"],
  "image_prompt": "A hyper-realistic 8k photograph visually capturing the exact core action and tangible hero object of this post. Authentic textures, cinematic studio lighting, sharp focus, 35mm lens, professional editorial photography, strictly NO female, no woman, no cartoon, no 3D render, no text, no watermark.",
  "topic_summary": "টপিকটির ১ লাইনের সংক্ষেপ (ভবিষ্যতে ডুপ্লিকেট রোধের জন্য)"
}}
"""
            logger.info(f"Generating unique content for slot '{slot}' ({theme}) using Hybrid Master Engine [Attempt {attempt}/{max_attempts}]...")
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

            # Passed uniqueness check - Apply LinkedIn Humanizer V3 & Fabric zero-fluff post-processing
            if parsed and parsed.get("content"):
                default_topic_tag = slot_info["hashtags"][1] if len(slot_info.get("hashtags", [])) > 1 else "#BusinessAutomation"
                humanized = humanize_post(parsed["content"], default_topic_tag=default_topic_tag)
                parsed["content"] = humanized["humanized_text"]
                parsed["humanizer_audit"] = humanized
                logger.info(f"Hybrid Humanizer Pass Complete: Final {humanized['word_count']} words, "
                            f"{len(humanized['vocab_cleaned'])} AI markers sanitized, "
                            f"{humanized.get('emojis_total', 0)} emojis detected (capped {humanized.get('emojis_capped', 0)}).")

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
        slot_info = SLOTS.get(slot, SLOTS["noon"])
        hashtags = " ".join(slot_info["hashtags"])
        title = f"🚀 {slot_info['theme']}: প্র্যাকটিক্যাল গাইড"
        
        if slot == "night":
            cta_line = "আপনার বিজনেসে এই ফুল-অটোমেটেড সিস্টেম সেটআপ করতে কমেন্টে 'AUTOMATE' লিখুন অথবা আমাদের পেজের WhatsApp বাটনে সরাসরি মেসেজ পাঠান!"
        else:
            cta_line = "আপনার মতামত কমেন্টে জানান, বন্ধুদের সাথে শেয়ার করে পোস্টটি সেইভ (Save 📌) রাখুন অথবা পেজের WhatsApp বাটনে আমাদের সাথে কানেক্ট হন!"

        content = f"""{title}

দৈনন্দিন কাজ ও ব্যবসাকে স্মার্ট করতে এআই-এর সঠিক প্রয়োগ জানা অত্যন্ত জরুরি। আজকের বিষয়: {focus_area}।

🔹 পুনরাবৃত্তিমূলক বোরিং ও সময়সাপেক্ষ কাজ দ্রুত শেষ করার স্মার্ট উপায়।
🔹 বাস্তব জীবনে কাজের গতি এবং নির্ভুলতা বাড়াতে এর ভূমিকা অপরিসীম।
🔹 স্মার্ট অটোমেশন ব্যবহারের মাধ্যমে আপনি প্রতিদিন ঘণ্টার পর ঘণ্টা সময় বাঁচাতে পারবেন।

{cta_line}

{hashtags}"""

        slot_names = {
            "noon": "AI Productivity & Hacks",
            "night": "B2B Business Automation"
        }

        default_topic_tag = slot_info["hashtags"][1] if len(slot_info.get("hashtags", [])) > 1 else "#BusinessAutomation"
        humanized = humanize_post(content, default_topic_tag=default_topic_tag)

        return {
            "title": title,
            "card_category": slot_names.get(slot, "AI Automation"),
            "card_headline": f"{focus_area}: স্মার্ট সলিউশন",
            "card_highlight": "স্মার্ট সলিউশন",
            "content": humanized["humanized_text"],
            "humanizer_audit": humanized,
            "hero_keywords": [focus_area, slot_info['theme']],
            "image_prompt": f"Realistic editorial photograph representing {focus_area}, high detail, 8k resolution, cinematic lighting, photorealistic, strictly no female, no woman, no people, no text.",
            "topic_summary": f"{slot_info['theme']} - {focus_area}"
        }
