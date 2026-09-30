<div align="center">

# 📢 Be Smart With AI — Autonomous Social Media Engine

**An event-driven, zero-touch AI content generation and publishing pipeline powered by Large Language Models, GitHub Actions, and the Meta Graph API.**

<p align="center">
  <img src="https://img.shields.io/badge/AI_Automation-Zero_Touch-7C3AED?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
  <img src="https://img.shields.io/badge/Meta_Graph_API-Auto_Publish-1877F2?style=for-the-badge&logo=facebook&logoColor=white" />
</p>

</div>

---

## 🌟 Pipeline Overview

Maintaining a high-authority technology brand requires consistent, high-value content. The **Be Smart With AI Auto-Poster Engine** runs autonomously on a scheduled cron pipeline via **GitHub Actions**. It researches trending AI & business automation topics, checks historical state (`post_history.json`) to prevent duplication, synthesizes engaging Bengali/English educational posts with custom visuals, and publishes directly to the official Facebook Page.

---

## 🏗️ Autonomous Workflow

```mermaid
flowchart TD
    Cron(["⏰ Scheduled Cron Trigger
(GitHub Actions)"]) --> History["📂 Deduplication Check
(post_history.json)"]
    History --> LLM["🧠 AI Content & Prompt Strategist
(LLM Engine)"]
    LLM --> Visual["🎨 Automated Visual Asset Generator"]
    LLM --> Copy["✍️ High-Conversion Bengali Post Copy"]
    Visual & Copy --> Meta["🌐 Meta Graph API Publisher"]
    Meta --> Page(["📱 Official Facebook Page
(@besmartwithaipro)"])
    Meta --> Commit["🔄 Auto-Commit Updated History [skip ci]"]
```

---

## ✨ Key Engineering Highlights

- **100% Serverless Execution:** Runs entirely on scheduled GitHub Actions runners with zero server maintenance overhead.
- **Stateful Deduplication:** Tracks every published topic and timestamp in version-controlled JSON state so content is never repeated.
- **Encrypted Secrets Management:** API keys and Meta Page Access Tokens are injected exclusively at runtime via GitHub Encrypted Secrets.

---

## 👨‍💻 Architected By

**Jubayer Ahamed**  
*AI Automation & Software Solutions Specialist | Founder @ [Be Smart With AI](https://www.facebook.com/besmartwithaipro)*

- 💬 **WhatsApp Direct:** [+880 1610-594042](https://wa.me/8801610594042)
- 🌐 **Facebook Page:** [Be Smart With AI](https://www.facebook.com/besmartwithaipro)
- 📧 **Email:** [sbmc4042@gmail.com](mailto:sbmc4042@gmail.com)
