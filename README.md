# Seller AI

[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-async-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![OpenAI](https://img.shields.io/badge/AI-GPT-412991?logo=openai&logoColor=white)](https://openai.com/)
[![FAISS](https://img.shields.io/badge/RAG-FAISS-005571)](https://github.com/facebookresearch/faiss)
[![License: Source-Available](https://img.shields.io/badge/license-Source--Available-orange)](LICENSE)

**English** | [Русский](README.ru.md)

**AI sales agent for Bitrix24 and amoCRM.** GPT talks to customers directly in the CRM chat, classifies leads, moves them through the sales pipeline, books meetings and re-engages dormant leads - all inside one system.

> Full pipeline: CRM webhook → GPT lead classification → answer via RAG over the company knowledge base → automatic actions (book a meeting, change the stage, call an external service). 5+ companies, different CRMs, different domains - one system.

---

## What's inside

Most "GPT sales bots" do one of two things:
1. Reply with keyword-matched templates - the customer quickly realizes they are talking to a bot.
2. Wrap GPT with no memory, no company knowledge and no actions - it writes text but does nothing with the lead in the CRM.

**Seller AI takes a different approach.** The bot is embedded in the CRM as a full participant: it sees the whole lead context (conversation history, pipeline stage, contact fields), answers from the client's knowledge base via RAG, and takes actions itself - books meetings, moves the lead through stages, calls integrations.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Pipeline                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CRM event ──► webhook ──► RequestDataHandler                              │
│                                       │                                     │
│                                       ▼                                     │
│                          resolve company + lead                             │
│                          by auth_domain / client_id                         │
│                                       │                                     │
│                                       ▼                                     │
│                          build conversation history                         │
│                          (build_history → max_history_length)               │
│                                       │                                     │
│                                       ▼                                     │
│                          FAISS retrieve - find                              │
│                          relevant knowledge base chunks                     │
│                                       │                                     │
│                                       ▼                                     │
│                          GPT + function calling                             │
│                          (create_meeting, change_funnel_stage,              │
│                           classify_lead, …)                                 │
│                                       │                                     │
│                       ┌───────────────┼───────────────┐                     │
│                       ▼               ▼               ▼                     │
│              send reply to      run a function    update the lead           │
│              the CRM chat       (Celery task)     pipeline stage            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

In parallel, a Celery beat "alarm clock" scans leads once a day for those with no activity for `sleep_days` and starts a re-engagement message from a configured template.

---

## Features

- **GPT in the CRM chat** - replies to customers directly in Bitrix24 Open Lines or amoCRM Chats, with the full conversation history as context.
- **Lead segmentation** - automatic A/B/C classification plus a status (New, Hot, Warm, Cold, Bought, Did not buy) based on conversation analysis.
- **RAG over the knowledge base** - a FAISS index of the company's documents. GPT answers from their content instead of making things up.
- **Function calling** - GPT decides when to call `create_meeting`, `change_funnel_stage`, `notify_manager` and others. Functions are configured per company in the admin panel.
- **Dormant lead "alarm clock"** - Celery beat brings back leads with no activity for N days. A daily limit prevents flooding.
- **Bitrix24 widget** - "Enable/Disable GPT for this contact" buttons right in the lead card.
- **Multi-tenant** - one installation serves several companies. Each has its own webhook, knowledge base, functions, prompts and time zone.
- **Pluggable CRMs** - Bitrix24 (REST + Open Lines + Placement) and amoCRM (OAuth + Chats API). New CRMs are added via `crm.services.crm_abs.CRM`.
- **Optional external integrations** - example: `crm/services/realty_api/`, a vendor-neutral client for a partner real-estate API, configured via env.

---

## Stack

| Layer | Technologies |
|---|---|
| Backend | Django 5.2, Django REST Framework, Python 3.12 |
| AI / LLM | OpenAI GPT (function calling), tiktoken, langchain |
| RAG | FAISS, OpenAI embeddings, langchain-community |
| Queues | Celery + django-celery-beat + Redis |
| DB | PostgreSQL |
| CRM SDKs | Bitrix24 REST API, amoCRM v4 |
| Deployment | Docker Compose, Gunicorn, Nginx |

---

## Project structure

```
chat/                        Conversations and GPT
  models.py                  Chat, Message, Func, Property
  services/
    base.py                  GPT wrapper, main reply pipeline
    build_history.py         Conversation history within the length limit
    documents.py             RAG: FAISS index + retrieve
    funcs.py                 Function calling: registration and dispatch
    settings.py              GPT model and parameters
  tasks.py                   Celery: dormant lead re-engagement
  templates/bitrix/          install.html + widget.html for the Bitrix24 embed
crm/
  models.py                  Lead with segmentation
  views.py                   WebhookView - main entry point from the CRM
  analyze.py                 GPT lead classification A/B/C
  services/
    crm_abs.py               Abstract CRM integration class
    request_data_handler.py  Incoming webhook parsing
    bitrix/                  Bitrix24 implementation
    amo/                     amoCRM implementation
    lead/                    Custom fields, lead domain operations
    outgoing.py              Outgoing messages and stage reactions
    realty_api/              Optional partner real-estate API
users/
  models.py                  Company, User, AMOConfig, FunnelStep
  admin.py                   Custom admin
  templates/stats/           Per-company statistics
conf/                        Django settings, Celery, middleware
```

---

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/webhook/`                          | Main CRM webhook (lead/message events) |
| `POST` | `/chat/webhook/enable-gpt/`          | Enable GPT for a specific contact |
| `POST` | `/chat/webhook/disable-gpt/`         | Disable GPT for a specific contact |
| `POST` | `/chat/bitrix/install/`              | Install the app in Bitrix24 (placement.bind) |
| `POST` | `/chat/bitrix/widget/`               | GPT control widget in the contact card |
| `GET`  | `/company/stats`                     | Company summary statistics |

See `chat/urls.py`, `crm/urls.py`, `users/urls.py` for details.

---

## Quick start

```bash
git clone https://github.com/AndreySukhanov/crm-seller-ai.git
cd crm-seller-ai
cp .env.example .env  # fill in SECRET_KEY, OPENAI_API_KEY, POSTGRES_*, REDIS_*

docker-compose up -d            # PostgreSQL + Redis
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# In separate terminals:
celery -A conf worker -l info
celery -A conf beat -l info
```

Open `http://localhost:8000/admin/`, create a company (Bitrix24 domain, webhook, prompt) and upload the knowledge base documents.

---

## Configuration

Key environment variables:

| Env | Value | Purpose |
|---|---|---|
| `SECRET_KEY`           | Django secret               | Session and signing cryptography |
| `DEBUG`                | `False` in production       | Debug mode |
| `ALLOWED_HOSTS`        | `yourdomain.com,…`          | Hosts Django responds to |
| `OPENAI_API_KEY`       | `sk-…`                      | OpenAI key |
| `OPENAI_BASE_URL`      | proxy URL (optional)        | Alternative base_url for an OpenAI-compatible gateway. Empty - call api.openai.com directly |
| `DEEP_SEEK_API_KEY`    | (optional)                  | DeepSeek as a fallback |
| `POSTGRES_*`           | DB settings                 | engine/db/user/password/host/port |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | | Celery backend |
| `APP_BASE_URL`         | `https://your.app.com`      | Public app URL (required by the Bitrix24 iframe widget) |
| `REALTY_API_BASE_URL`  | partner URL (optional)      | If the real-estate service integration is enabled |

---

## Adding a new CRM

1. Subclass `crm.services.crm_abs.CRM`.
2. Implement the abstract methods: `send_message_to_chat`, `change_funnel_stage`, `create_meeting`, …
3. Register it in `crm.services.request_data_handler.get_crm()`.
4. Add incoming webhook parsing to `RequestDataHandler`.

---

## Deployment

See `DEPLOYMENT.md` (Gunicorn + Nginx + systemd, PostgreSQL backups, certbot, Celery monitoring; in Russian).

---

## License

[Source-Available](LICENSE). Reading, studying and learning from the code - yes; using it in products or services without written permission - no. Licensing questions: `avsukhanov21@gmail.com`.
