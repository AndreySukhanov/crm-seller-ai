# Seller AI

[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-async-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![OpenAI](https://img.shields.io/badge/AI-GPT-412991?logo=openai&logoColor=white)](https://openai.com/)
[![FAISS](https://img.shields.io/badge/RAG-FAISS-005571)](https://github.com/facebookresearch/faiss)
[![License: Source-Available](https://img.shields.io/badge/license-Source--Available-orange)](LICENSE)

**AI-продавец для Bitrix24 и AMO CRM.** GPT ведёт диалоги с клиентами прямо в чате CRM, классифицирует лидов, двигает их по воронке, назначает встречи и возвращает «спящих» — всё внутри одной системы.

> Полный pipeline: webhook от CRM → классификация лида GPT → ответ через RAG по базе знаний компании → автодействия (создать встречу, перевести стадию, дернуть внешний сервис). 5+ компаний, разные CRM, разные домены — одна система.

---

## Что внутри

Большинство «GPT-продавцов» делают одно из двух:
1. Отвечают шаблонами по ключевым словам — клиент быстро понимает, что говорит с ботом.
2. Делают «GPT-обёртку» без памяти, без знаний компании, без действий — пишет тексты, но ничего не делает с лидом в CRM.

**Seller AI делает иначе.** Бот вшит в CRM как полноценный участник: видит весь контекст лида (история переписки, стадия воронки, поля контакта), отвечает на основе базы знаний клиента через RAG, и сам совершает действия — создаёт встречу, двигает по этапам, дёргает интеграции.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Pipeline                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CRM event ──► webhook ──► RequestDataHandler                              │
│                                       │                                     │
│                                       ▼                                     │
│                          определить компанию + лида                         │
│                          по auth_domain / client_id                         │
│                                       │                                     │
│                                       ▼                                     │
│                          собрать историю диалога                            │
│                          (build_history → max_history_length)               │
│                                       │                                     │
│                                       ▼                                     │
│                          FAISS retrieve — найти                             │
│                          релевантные куски базы знаний                      │
│                                       │                                     │
│                                       ▼                                     │
│                          GPT + function calling                             │
│                          (create_meeting, change_funnel_stage,              │
│                           classify_lead, …)                                 │
│                                       │                                     │
│                       ┌───────────────┼───────────────┐                     │
│                       ▼               ▼               ▼                     │
│              отправить ответ    выполнить функцию   обновить стадию         │
│              в чат CRM          (Celery task)       лида в воронке          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

Параллельно работает Celery beat «будильник» — раз в сутки сканирует лидов, у которых нет активности `sleep_days`, и инициирует возврат через настроенный шаблон.

---

## Возможности

- **GPT в чате CRM** — отвечает клиентам прямо в Bitrix24 OpenLines или AMO Chats. Понимает контекст всей истории диалога.
- **Сегментация лидов** — автоматическая классификация A/B/C + статус (Новый, Горячий, Тёплый, Холодный, Купил, Не купил) по результату анализа диалога.
- **RAG поверх базы знаний** — FAISS-индекс с документами компании. GPT отвечает на основе их содержимого, не выдумывает.
- **Function calling** — GPT сам решает, когда вызвать `create_meeting`, `change_funnel_stage`, `notify_manager` и др. Функции настраиваются на стороне админки для каждой компании.
- **«Будильник» для спящих лидов** — Celery beat возвращает в диалог тех, у кого не было активности N дней. Дневной лимит, чтобы не флудить.
- **Виджет в Bitrix24** — кнопки «Включить/Выключить GPT для контакта» прямо в карточке лида.
- **Multi-tenant** — одна установка обслуживает несколько компаний. У каждой свой webhook, своя база знаний, свои функции, свои промпты, свой часовой пояс.
- **Подключаемые CRM** — Bitrix24 (REST + OpenLines + Placement) и AMO CRM (OAuth + Chats API). Новые CRM добавляются через `crm.services.crm_abs.CRM`.
- **Опциональные внешние интеграции** — пример: `crm/services/realty_api/` — вендор-независимый клиент партнёрской API недвижимости, конфигурируется через env.

---

## Стек

| Слой | Технологии |
|---|---|
| Backend | Django 5.2, Django REST Framework, Python 3.12 |
| AI / LLM | OpenAI GPT (function calling), tiktoken, langchain |
| RAG | FAISS, OpenAI embeddings, langchain-community |
| Очереди | Celery + django-celery-beat + Redis |
| БД | PostgreSQL |
| CRM SDKs | Bitrix24 REST API, AMO CRM v4 |
| Деплой | Docker Compose, Gunicorn, Nginx |

---

## Структура проекта

```
chat/                        Модуль диалогов и GPT
  models.py                  Chat, Message, Func, Property
  services/
    base.py                  GPT-обёртка, основной pipeline ответа
    build_history.py         Сборка истории диалога с учётом лимита
    documents.py             RAG: FAISS-индекс + retrieve
    funcs.py                 Function calling: регистрация и вызов
    settings.py              Модель/параметры GPT
  tasks.py                   Celery: возврат спящих лидов
  templates/bitrix/          install.html + widget.html для встройки в Bitrix
crm/
  models.py                  Lead с сегментацией
  views.py                   WebhookView — основная точка входа из CRM
  analyze.py                 GPT-классификация лидов A/B/C
  services/
    crm_abs.py               Абстрактный класс CRM-интеграции
    request_data_handler.py  Парсинг входящих webhook
    bitrix/                  Реализация для Bitrix24
    amo/                     Реализация для AMO CRM
    lead/                    Custom fields, доменные операции с лидом
    outgoing.py              Исходящие сообщения и реакции на стадии
    realty_api/              Опц. партнёрская API недвижимости
users/
  models.py                  Company, User, AMOConfig, FunnelStep
  admin.py                   Кастомная админка
  templates/stats/           Статистика по компаниям
conf/                        Django settings, Celery, middleware
```

---

## API

| Метод | Путь | Назначение |
|---|---|---|
| `POST` | `/webhook/`                          | Основной webhook от CRM (lead/message events) |
| `POST` | `/chat/webhook/enable-gpt/`          | Включить GPT для конкретного контакта |
| `POST` | `/chat/webhook/disable-gpt/`         | Выключить GPT для конкретного контакта |
| `POST` | `/chat/bitrix/install/`              | Установка приложения в Bitrix24 (placement.bind) |
| `POST` | `/chat/bitrix/widget/`               | Виджет управления GPT в карточке контакта |
| `GET`  | `/company/stats`                     | Сводная статистика компании |

Подробнее — в `chat/urls.py`, `crm/urls.py`, `users/urls.py`.

---

## Быстрый старт

```bash
git clone https://github.com/AndreySukhanov/seller-ai.git
cd seller-ai
cp .env.example .env  # заполнить SECRET_KEY, OPENAI_API_KEY, POSTGRES_*, REDIS_*

docker-compose up -d            # PostgreSQL + Redis
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# В отдельных терминалах:
celery -A conf worker -l info
celery -A conf beat -l info
```

Открыть `http://localhost:8000/admin/`, завести компанию (домен Bitrix24, webhook, промпт), залить документы базы знаний.

---

## Конфигурация

Ключевые переменные окружения:

| Env | Значение | Назначение |
|---|---|---|
| `SECRET_KEY`           | Django secret               | Криптография сессий и подписи |
| `DEBUG`                | `False` в проде             | Режим отладки |
| `ALLOWED_HOSTS`        | `yourdomain.com,…`          | Хосты, на которые отвечает Django |
| `OPENAI_API_KEY`       | `sk-…`                      | Ключ OpenAI |
| `OPENAI_BASE_URL`      | URL прокси (опц.)           | Альтернативный base_url для OpenAI-совместимого шлюза. Пусто — обращаемся к api.openai.com напрямую |
| `DEEP_SEEK_API_KEY`    | (опц.)                      | DeepSeek как fallback |
| `POSTGRES_*`           | DB настройки                | engine/db/user/password/host/port |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | | Backend для Celery |
| `APP_BASE_URL`         | `https://your.app.com`      | Внешний URL приложения (нужен Bitrix iframe-виджету) |
| `REALTY_API_BASE_URL`  | URL партнёра (опц.)         | Если включена интеграция с сервисом недвижимости |

---

## Добавление новой CRM

1. Наследуйтесь от `crm.services.crm_abs.CRM`.
2. Реализуйте абстрактные методы: `send_message_to_chat`, `change_funnel_stage`, `create_meeting`, …
3. Зарегистрируйте в `crm.services.request_data_handler.get_crm()`.
4. Добавьте парсинг входящего webhook в `RequestDataHandler`.

---

## Деплой

Подробнее — `DEPLOYMENT.md` (Gunicorn + Nginx + systemd, бэкапы PostgreSQL, certbot, мониторинг Celery).

---

## Лицензия

[Source-Available](LICENSE). Читать, изучать, учиться — да; использовать в продуктах/сервисах без письменного разрешения — нет. По вопросам лицензирования: `avsukhanov21@gmail.com`.
