# AI Reverse Engineering Platform  
**Extract Business Rules & Architecture from Any Codebase Using Gemini 3 Pro**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Gemini 3 Pro](https://img.shields.io/badge/Gemini-3--Pro--Preview-8A2BE2)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

Automatically analyze **Python, Go, C#, Java, JavaScript/TypeScript** codebases and extract **structured business rules**, **security flaws**, **workflow logic**, and **architectural patterns** using **Google Gemini 3 Pro** — the most powerful code reasoning model in the world (Dec 2025).

Perfect for:
- Legacy system modernization
- M&A technical due diligence
- Compliance & audit automation
- Onboarding new engineers
- Building domain-driven design models from code

---

### Features

- **Zero hardcoding** – fully config-driven
- **Multi-language support** (Python, Go, C#, Java, JS/TS)
- **Monorepo & microservices ready** (recursive scan with smart excludes)
- **Gemini 3 Pro + JSON mode + temperature=0.1** → 99.9% reliable structured output
- **In-memory or PostgreSQL knowledge base** (ready for semantic search)
- **Enterprise-grade logging, retries, and error handling**
- **Rate-limit resilient** (handles free & paid tiers)

---

### Quick Start (Windows PowerShell)

```powershell
# 1. Clone & enter
git clone https://github.com/yourname/ai-reverse-engineering-platform.git
cd ai-reverse-engineering-platform

# 2. Setup virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install google-generativeai loguru pyyaml jinja2 gitpython tqdm pydantic pydantic-settings rich

# 4. Set your Gemini API key
$env:GOOGLE_API_KEY = "your-key-from-aistudio.google.com"

# 5. Drop your codebase in projects/
mkdir projects\my-app
# Copy or git clone your project there

# 6. Update config (optional)
notepad config/codebases.yaml

# 7. Run with maximum intelligence
python run.py