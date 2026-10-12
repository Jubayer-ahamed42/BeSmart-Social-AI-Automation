# 📘 ফেসবুক অটো-পোস্টার সেটআপ গাইড (Step-by-Step Bangla Guide)

এই গাইডটি অনুসরণ করে আপনি মাত্র ১০-১৫ মিনিটে আপনার ফেসবুক পেজের জন্য সম্পূর্ণ স্বয়ংক্রিয় বটটি ক্লাউডে চালু করে দিতে পারবেন। একবার সেটআপ শেষ হলে আপনাকে কম্পিউটারও অন রাখতে হবে না, প্রতিদিন নির্দিষ্ট সময়ে স্বয়ংক্রিয়ভাবে ক্লাউড থেকে পোস্ট পাবলিশ হতে থাকবে।

---

## 🧭 আপনার মোট ৩টি তথ্য (Secrets) প্রয়োজন:
1. `GEMINI_API_KEY` (পোস্টের লেখা তৈরি করার ফ্রি এআই কি)
2. `FB_PAGE_ID` (আপনার ফেসবুক পেজের আইডি নম্বর)
3. `FB_PAGE_ACCESS_TOKEN` (ফেসবুক পেজে পোস্ট করার স্থায়ী এক্সেস টোকেন)

---

## ধাপ ১: Google Gemini API Key সংগ্রহ (১ মিনিট)
1. ব্রাউজারে যান: [https://aistudio.google.com/](https://aistudio.google.com/)
2. আপনার গুগল (Gmail) অ্যাকাউন্ট দিয়ে লগইন করুন।
3. বাম পাশের মেনু থেকে **"Get API key"** বাটনে ক্লিক করুন।
4. **"Create API key"**-তে ক্লিক করে তৈরি হওয়া কি (Key)-টি কপি করে একটি নিরাপদ নোটে সংরক্ষণ করুন।
*(গুগল জেমিনি এপিআই সম্পূর্ণ ফ্রি এবং কোনো ক্রেডিট কার্ড লাগে না)*

---

## ধাপ ২: Facebook Page ID সংগ্রহ (১ মিনিট)
1. আপনার ফেসবুক পেজে যান।
2. পেজের **About** ট্যাবে যান, অথবা পেজের সেটিংসে যান।
3. সেখানে **Page ID** দেখতে পাবেন (যেমন: `104829384729104` ধরণের ১৫-১৬ ডিজিটের একটি সংখ্যা)।
4. এটি কপি করে রাখুন।

---

## ধাপ ৩: Facebook Page Access Token সংগ্রহ (মেয়াদহীন টোকেন)
ফেসবুকে কোনো অ্যাপ দিয়ে স্বয়ংক্রিয়ভাবে পোস্ট করার জন্য Meta Graph API টোকেন প্রয়োজন:

### ৩.১ একটি মেটা ডেভেলপার অ্যাপ তৈরি:
1. যান: [https://developers.facebook.com/](https://developers.facebook.com/)
2. ডানদিকের উপরে **"My Apps"**-এ ক্লিক করুন।
3. **"Create App"** বাটনে ক্লিক করুন।
4. Use case হিসেবে **"Other"** সিলেক্ট করে Next দিন।
5. App type হিসেবে **"Business"** সিলেক্ট করে Next দিন।
6. অ্যাপের একটি নাম দিন (যেমন: `My Page Auto Poster`) এবং Create App ক্লিক করুন।

### ৩.২ Graph API Explorer থেকে পারমিশন ও টোকেন নেওয়া:
1. ব্রাউজারে যান: [https://developers.facebook.com/tools/explorer/](https://developers.facebook.com/tools/explorer/)
2. ডানপাশে **"Meta App"** ড্রপডাউনে আপনার তৈরি করা অ্যাপটি সিলেক্ট করুন।
3. **"Permissions"** সেকশনে ক্লিক করে নিচের ৩টি পারমিশন যোগ করুন:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
4. **"Generate Access Token"** বাটনে ক্লিক করুন এবং ফেসবুকে অনুমতি দিন।
5. এরপর **"User or Page"** ড্রপডাউনে ক্লিক করে **আপনার ফেসবুক পেজটি** নির্বাচন করুন।
6. এবার যে টোকেনটি দেখতে পাবেন, সেটিই আপনার পেজের টোকেন।

### ৩.৩ টোকেনটিকে আজীবন স্থায়ী (Never-Expiring) করা:
1. যান: [https://developers.facebook.com/tools/debug/accesstoken/](https://developers.facebook.com/tools/debug/accesstoken/)
2. আপনার পাওয়া টোকেনটি পেস্ট করে **"Debug"** বাটনে ক্লিক করুন।
3. নিচে **"Extend Access Token"** অপশন পাবেন, তাতে ক্লিক করলে একটি লং-লিভড (Long-lived) টোকেন জেনারেট হবে।
4. এই পদ্ধতিতে পেজের পাওয়া টোকেনটি **"Never Expires"** বা আজীবন মেয়াদের হয়ে যায়। এটি কপি করে সংরক্ষণ করুন।

---

## ধাপ ৪: লোকাল কম্পিউটারে টেস্ট করা (ঐচ্ছিক কিন্তু দারুণ)
বটটি আপনার কম্পিউটারে টেস্ট করতে চাইলে:
1. প্রজেক্ট ফোল্ডারে থাকা `.env.example` ফাইলের নাম পরিবর্তন করে `.env` করুন।
2. ভেতরে আপনার কি-গুলো বসিয়ে সেভ করুন:
   ```env
   GEMINI_API_KEY=AIzaSy...
   FB_PAGE_ID=1029384756...
   FB_PAGE_ACCESS_TOKEN=EAAG...
   ```
3. এবার টার্মিনালে রান করুন:
   - সংযোগ পরীক্ষা করতে:
     ```bash
     python main.py --verify
     ```
   - একটি পোস্ট ও ছবি প্রিভিউ দেখতে (ফেসবুকে পোস্ট হবে না):
     ```bash
     python main.py --dry-run
     ```
   - সরাসরি ফেসবুকে পোস্ট করতে:
     ```bash
     python main.py
     ```

---

## ধাপ ৫: GitHub Actions ক্লাউড সেটআপ (সম্পূর্ণ অটোমেশন ২৪/৭)
এই ধাপে আপনি কোডটি GitHub-এ আপলোড করবেন, যাতে আপনার কম্পিউটার বন্ধ থাকলেও GitHub নিজে নিজে প্রতিদিন সকাল ৭টা, দুপুর ১২টা, বিকাল ৪টা ও রাত ৮টায় পোস্ট করে দেয়!

1. [https://github.com/](https://github.com/) এ গিয়ে একটি নতুন **Private** রিপোজিটরি তৈরি করুন (যেমন: `facebook-auto-poster`)।
2. আপনার এই লোকাল ফোল্ডারের কোডগুলো GitHub-এ পুশ (Push) করুন:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Facebook auto poster"
   git branch -M main
   git remote add origin https://github.com/আপনার-ইউজারনেম/facebook-auto-poster.git
   git push -u origin main
   ```
3. এবার GitHub রিপোজিটরির **Settings** ট্যাবে যান।
4. বাম পাশের মেনু থেকে **Secrets and variables** -> **Actions** এ ক্লিক করুন।
5. **"New repository secret"** এ ক্লিক করে নিচের ৩টি সিক্রেট আলাদা আলাদাভাবে যোগ করুন:
   - Name: `GEMINI_API_KEY` | Value: আপনার জেমিনি কি
   - Name: `FB_PAGE_ID` | Value: আপনার পেজ আইডি
   - Name: `FB_PAGE_ACCESS_TOKEN` | Value: আপনার ফেসবুক পেজ টোকেন
6. এবার **Settings** -> **Actions** -> **General** এ গিয়ে নিচের দিকে **"Workflow permissions"** সেকশনে **"Read and write permissions"** সিলেক্ট করে Save দিন (যাতে পোস্টের হিস্ট্রি আপডেট গিটহাবে সেভ হতে পারে)।

---

## 🎉 অভিনন্দন! আপনার কাজ শেষ!
- বটটি এখন ক্লাউডে জীবিত এবং পুরোপুরি স্বয়ংক্রিয়।
- প্রতিদিন **বাংলাদেশ সময় সকাল ০৭:০০ টায় AI**, **দুপুর ১২:০০ টায় Technology & Gadgets**, **বিকাল ০৪:০০ টায় Cybersecurity & Smart Tech**, এবং **রাত ০৮:০০ টায় Science & Deep Space** নিয়ে বাস্তবসম্মত আকর্ষণীয় ছবি সহ পোস্ট করবে।
- যে কোনো সময় তাৎক্ষণিক একটি পোস্ট করতে চাইলে: GitHub রিপোজিটরির **Actions** ট্যাবে গিয়ে **"Facebook Page 24/7 Autonomous Poster"** সিলেক্ট করে **"Run workflow"** বাটনে ক্লিক করলেই মুহূর্তের মধ্যে পোস্ট হয়ে যাবে!
