# Intelligent Commercial Logistics Platform (ICLP) MCP Server

<div align="center">

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

</div>

---

## 🎯 Project Vision
A **premium‑grade**, **real‑time analytics** engine that ingests Zoho Creator freight enquiry records, enriches them with deterministic logistics metrics, and augments the data with **large‑language‑model (LLM)** insights. The resulting intelligence is pushed back to Zoho, enabling sales & pricing teams to act on **actionable, AI‑driven recommendations** in seconds.

---

## 📦 Core Features
- **FastAPI‑powered webhook** that guarantees a sub‑2.5 s SLA by off‑loading heavy LLM work to background tasks.
- **Deterministic metric engine** (`calculate_operational_metrics`) for turnaround delays, cutoff breaches, and win‑rate calculations.
- **LLM orchestration** with two specialized models:
  - **Model A** – strict JSON analytics dashboard payload.
  - **Model B** – polished B2B quotation email body.
- **Graceful fallback** to deterministic mock responses when OpenAI credentials are missing or the API fails.
- **Zoho Creator integration** – dry‑run mode for local development and live PATCH updates for production.
- **Extensible design** – plug‑in new tools via the `@mcp_server.tool()` decorator.

---

## 🏗️ Architecture Overview
<div align="center">

![ICLP Architecture](file:///C:/Users/Joy%20Magdalene%20A/OneDrive/Desktop/iclp-mcp-server/docs/architecture.png)

</div>

> **Figure:** High‑level data flow – from Zoho webhook → FastAPI → deterministic engine → LLM orchestration → Zoho update.

*If the image is missing, run the `generate_image` tool to create a diagram.*

---

## ⚙️ Prerequisites
| Tool | Version |
|------|---------|
| Python | ≥ 3.10 |
| FastAPI | 0.112.0 |
| Uvicorn (ASGI server) | latest |
| OpenAI client (optional) | `openai>=1.0.0` |
| `dotenv` for local env handling |

---

## 🚀 Getting Started
1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/iclp-mcp-server.git
   cd iclp-mcp-server
   ```
2. **Create a virtual environment & install dependencies**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
3. **Configure environment variables** – copy the example and fill in your Zoho & OpenAI credentials:
   ```bash
   cp .env.example .env
   # edit .env (ZOHO_*, OPENAI_API_KEY, etc.)
   ```
4. **Run the development server**
   ```bash
   uvicorn app:app --reload
   ```
   The API will be reachable at `http://127.0.0.1:8000`.

---

## 📚 API Reference
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/webhooks/v1/enquiry` | Accepts a `ZohoEnquiryPayload`, validates, and queues the analytics pipeline.
| `GET`  | `/health` | Simple health‑check returning `{ status: "healthy" }`.
| `GET`  | `/` | Root welcome message with version & docs link.

**Live OpenAPI docs**: `http://127.0.0.1:8000/docs`

---

## 🛠️ Development Tips
- **Background tasks** – the heavy LLM call runs in a FastAPI `BackgroundTasks` worker. Adjust the thread pool size via `uvicorn --workers N` if you anticipate high webhook throughput.
- **Dry‑run mode** – when any Zoho credential is missing, the server prints the payload that *would* be PATCHed. This is safe for local testing.
- **Logging** – replace `print` statements with Python `logging` for production‑grade observability.
- **Unit tests** – a minimal pytest suite lives under `tests/`. Run `pytest -q` after installing `pytest`.

---

## 🤝 Contributing
1. Fork the repo.
2. Create a feature branch (`git checkout -b feat/awesome‑feature`).
3. Write tests for your changes.
4. Submit a Pull Request with a clear description.

Please follow the **premium design guidelines** – consistent styling, meaningful docstrings, and type hints.

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for full text.

---

*Made with ❤️ by the ICLP engineering team.*
