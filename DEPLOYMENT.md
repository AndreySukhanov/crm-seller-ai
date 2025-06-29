# Инструкция по развертыванию

## Подготовка сервера

### 1. Установка системных зависимостей

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server

# CentOS/RHEL
sudo yum install python3 python3-pip nginx postgresql postgresql-server redis
```

### 2. Настройка PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE seller-ai;
CREATE USER sellerai_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE seller-ai TO sellerai_user;
\q
```

### 3. Настройка Redis

```bash
sudo systemctl enable redis
sudo systemctl start redis
```

## Развертывание приложения

### 1. Клонирование и настройка

```bash
cd /var/www/
git clone <repository-url> seller-ai
cd seller-ai/seller-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
nano .env
```

Заполните переменные:
```env
SECRET_KEY=generate-secure-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_DB=seller-ai
POSTGRES_USER=sellerai_user
POSTGRES_PASSWORD=secure_password
POSTGRES_HOST=localhost
OPENAI_API_KEY=your_openai_key
```

### 3. Применение миграций

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 4. Настройка Gunicorn

```bash
pip install gunicorn

# Тест запуска
gunicorn conf.wsgi:application --bind 0.0.0.0:8000
```

Создайте systemd service `/etc/systemd/system/seller-ai.service`:

```ini
[Unit]
Description=Seller-AI Django app
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/seller-ai/seller-ai
Environment="PATH=/var/www/seller-ai/seller-ai/venv/bin"
ExecStart=/var/www/seller-ai/seller-ai/venv/bin/gunicorn --workers 3 --bind unix:/var/www/seller-ai/seller-ai.sock conf.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 5. Настройка Nginx

Создайте `/etc/nginx/sites-available/seller-ai`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/seller-ai/seller-ai;
    }

    location /media/ {
        root /var/www/seller-ai/seller-ai;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/seller-ai/seller-ai.sock;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/seller-ai /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Запуск Celery

Создайте systemd service `/etc/systemd/system/seller-ai-celery.service`:

```ini
[Unit]
Description=Seller-AI Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/var/www/seller-ai/seller-ai/.env
WorkingDirectory=/var/www/seller-ai/seller-ai
ExecStart=/var/www/seller-ai/seller-ai/venv/bin/celery multi start worker1 \
    -A conf --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log --loglevel=INFO
ExecStop=/var/www/seller-ai/seller-ai/venv/bin/celery multi stopwait worker1 \
    --pidfile=/var/run/celery/%n.pid
ExecReload=/var/www/seller-ai/seller-ai/venv/bin/celery multi restart worker1 \
    -A conf --pidfile=/var/run/celery/%n.pid \
    --logfile=/var/log/celery/%n%I.log --loglevel=INFO

[Install]
WantedBy=multi-user.target
```

Создайте директории для логов:

```bash
sudo mkdir -p /var/run/celery /var/log/celery
sudo chown www-data:www-data /var/run/celery /var/log/celery
```

### 7. Запуск сервисов

```bash
sudo systemctl daemon-reload
sudo systemctl enable seller-ai
sudo systemctl enable seller-ai-celery
sudo systemctl start seller-ai
sudo systemctl start seller-ai-celery
```

## SSL сертификат (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Мониторинг

### Проверка статуса

```bash
sudo systemctl status seller-ai
sudo systemctl status seller-ai-celery
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis
```

### Логи

```bash
# Django логи
tail -f /var/log/celery/worker1.log

# Nginx логи
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Systemd логи
journalctl -u seller-ai -f
journalctl -u seller-ai-celery -f
```

## Backup

### База данных

```bash
# Создание бэкапа
pg_dump -U sellerai_user -h localhost seller-ai > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление
psql -U sellerai_user -h localhost seller-ai < backup_file.sql
```

### Файлы

```bash
# Создание архива
tar -czf seller-ai_backup_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/seller-ai/

# Исключая виртуальное окружение
tar --exclude='venv' -czf seller-ai_backup_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/seller-ai/
```

## Обновление

```bash
cd /var/www/seller-ai/seller-ai
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart seller-ai
sudo systemctl restart seller-ai-celery
``` 