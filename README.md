# 🤖 24/7 Autonomous Facebook Page Social Media Agent (Be Smart With AI)

An autonomous, AI-powered social media manager that publishes high-engagement Bengali posts with authentic high-resolution visuals directly to the Facebook Page **Be Smart With AI** twice a day on schedule.

Zero maintenance, zero server costs, and 100% cloud-hosted via **GitHub Actions** with local **Windows Task Scheduler** failover.

---

## 🕒 Dual-Slot Daily Schedule & Themes (Bangladesh Standard Time - UTC+6)

| Slot | Time (BST) | UTC | Target Audience & Theme | Focus Areas |
| :--- | :--- | :--- | :--- | :--- |
| **`noon`** | **12:00 PM** | 06:00 UTC | ⚡ **AI Productivity & Real-Life Automation**<br>*(দৈনন্দিন এআই অটোমেশন ও প্রোডাক্টিভিটি)* | ছাত্রছাত্রী, চাকরিজীবী ও ফ্রিল্যান্সারদের জন্য প্র্যাক্টিক্যাল এআই হ্যাকস, এক্সেল অটোমেশন, NotebookLM সামারি, Spoken English মক টেস্ট, ATS সিভি, আপওয়ার্ক প্রপোজাল। |
| **`night`** | **08:00 PM** | 14:00 UTC | 🤖 **B2B Business Automation & Scaling**<br>*(ব্যবসায়িক অটোমেশন ও গ্রোথ)* | ব্যবসায়ী, ই-কমার্স ওনার ও ফাউন্ডারদের জন্য ২৪/৭ সেলস বট, কুরিয়ার অটোমেশন (Steadfast/Pathao), সিওডি কনফার্মেশন, কোল্ড লিড রিকভারি, কাস্টমার সাপোর্ট কমানো। |

---

## 🚀 Key Features

- **100% Autonomous**: Runs on GitHub Actions scheduled cron with dual-slot redundancy and local Windows Task Scheduler backup.
- **Race Condition Immunity**: Real-time live Facebook Page feed check (`GET /{page_id}/feed?limit=3` / `published_posts`) verifies whether a post was already published today or within the last 2 hours, preventing duplicate postings between cloud runners and local machines.
- **Engaging Bengali Copywriting**: Google Gemini AI structured generation with catchy hooks, actionable bullet points, humanized conversational tone, and strictly controlled emojis & hashtags.
- **Editorial PhotoCard Engine**:
  - High-res photorealistic visual generation via FLUX AI.
  - Headless Chromium composition with 100% offline base64 embedded fonts (Hind Siliguri Bold + Plus Jakarta Sans).
  - Pristine base image fail-safe fallback preserving pure image quality without corrupt text overlays or broken Bengali conjuncts.
- **Strict Content & Visual Ethics**: Zero female depictions, zero AI cliches, sanitized prompts, and anti-glitch directives.
- **Smart Duplicate Prevention**: `post_history.json` tracks topics with Jaccard similarity and token overlap filtering to guarantee non-repeating content.
- **Manual Trigger**: Supports one-click manual posting directly from GitHub Actions web interface (`workflow_dispatch`).

---

## 📖 Setup Instructions

Detailed Bengali instructions are available in:
👉 **[SETUP_GUIDE_BANGLA.md](SETUP_GUIDE_BANGLA.md)**

### Required Secrets
1. `GEMINI_API_KEY`: Free Google AI Studio API key
2. `FB_PAGE_ID`: Target Facebook Page numeric ID
3. `FB_PAGE_ACCESS_TOKEN`: Long-lived Meta Graph API Page Access Token
4. `WHATSAPP_NUMBER`: WhatsApp business contact number (`8801610594042`)

---

## 💻 Local CLI Usage

```bash
# 1. Verify API credentials and Facebook connection
python main.py --verify

# 2. Dry run preview (does not publish to Facebook)
python main.py --dry-run

# 3. Test specific slot preview
python main.py --slot noon --dry-run
python main.py --slot night --dry-run

# 4. Run automated post now (auto detects slot based on current BST time)
python main.py --slot auto

# 5. Run full post for specific slot
python main.py --slot noon
python main.py --slot night

# 6. Force post (bypasses daily guards and live checks)
python main.py --slot noon --force
```

---

## 🧪 Comprehensive Verification Suite

Run all component and functional verification tests:
```bash
python test_runner.py
```
