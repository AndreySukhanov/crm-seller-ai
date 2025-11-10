# Нейропродавец AMO CRM

AI-powered продавец с интеграцией в CRM системы (Bitrix24, AMO CRM).

## Описание

Система автоматизации продаж с использованием GPT для:
- Автоматических ответов клиентам через CRM каналы
- Классификации и сегментации лидов  
- Создания встреч и управления воронкой продаж
- RAG (Retrieval-Augmented Generation) для базы знаний компании
- Автоматического возврата "спящих" лидов

## Основные возможности

- 🤖 **GPT-бот** для автоматических ответов клиентам
- 📊 **Сегментация лидов**: A/B/C + статусы (Новый, Горячий, Тёплый, Холодный, Купил, Не купил)
- 📅 **Умное планирование встреч** через CRM
- 🔄 **Автоматическое движение по воронке** на основе анализа диалогов
- 📚 **RAG система** для контекстных ответов на базе знаний
- ⏰ **"Будильник"** для возврата неактивных лидов
- 🎛️ **Виджет управления** прямо в CRM интерфейсе

## Технологии

- **Backend**: Django 5.2, PostgreSQL, Redis
- **AI**: OpenAI GPT-4, FAISS для векторного поиска
- **Очереди**: Celery для фоновых задач
- **CRM**: Bitrix24 REST API, AMO CRM
- **Контейнеризация**: Docker Compose

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <repository-url>
cd нейропродавец_битрикс/sellmind
```

### 2. Создание виртуальной среды

```bash
python -m venv myvenv
# Windows:
myvenv\Scripts\activate
# Linux/macOS:
source myvenv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка окружения

Скопируйте `.env.example` в `.env` и заполните переменные:

```bash
cp .env.example .env
```

Обязательные переменные:
- `SECRET_KEY` - Django секретный ключ
- `OPENAI_API_KEY` - API ключ OpenAI
- `POSTGRES_*` - настройки базы данных

### 5. Запуск инфраструктуры

```bash
docker-compose up -d  # PostgreSQL + Redis
```

### 6. Миграции и запуск

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 7. Запуск Celery (отдельный терминал)

```bash
celery -A conf worker -l info
celery -A conf beat -l info  # для периодических задач
```

## Настройка CRM

### Bitrix24

1. Создайте входящий вебхук в Bitrix24
2. В админке Django добавьте компанию с:
   - `auth_domain` - домен вашего Bitrix24 (например: `company.bitrix24.ru`)
   - `webhook` - URL вебхука Bitrix24

3. Установите приложение в Bitrix24:
   - URL установки: `https://yourdomain.com/chat/bitrix/install/`
   - URL обработчика: `https://yourdomain.com/webhook/`

## Структура проекта

```
sellmind/
├── chat/          # Модуль чата и GPT
├── crm/           # CRM интеграции
├── users/         # Пользователи и компании
├── conf/          # Настройки Django
├── utils/         # Общие утилиты
└── templates/     # HTML шаблоны
```

## API Endpoints

- `POST /webhook/` - Основной webhook для CRM событий
- `POST /chat/webhook/disable-gpt/` - Отключение GPT
- `POST /chat/webhook/enable-gpt/` - Включение GPT
- `GET /company/stats` - Статистика компании

## Разработка

### Структура моделей

- **Company** - Настройки компании
- **User** - Пользователи из CRM
- **Lead** - Лиды с сегментацией
- **Chat/Message** - История переписки
- **Func/Property** - Функции для GPT

### Добавление новой CRM

1. Наследуйте от `crm.services.crm_abs.CRM`
2. Реализуйте все абстрактные методы
3. Добавьте в `crm.services.request_data_handler.get_crm()`

## Производственная среда

### Настройки безопасности

```python
# .env для production
DEBUG=False
SECRET_KEY=<secure-random-key>
ALLOWED_HOSTS=yourdomain.com
```

### Nginx конфигурация

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Мониторинг

Логи находятся в:
- `logs/app.log` - основные логи приложения
- Console output для разработки

## Лицензия

Проприетарное ПО

## Поддержка

При возникновении проблем проверьте:
1. Логи в `logs/app.log`
2. Статус сервисов: `docker-compose ps`
3. Настройки CRM вебхуков
4. Переменные окружения в `.env` 
