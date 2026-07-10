# RPI Student Government Website

Wagtail 7.3 CMS on Django 6.0.

## Development

**Prerequisites:** Python 3.12, Node 20

```bash
# Python environment
python -m venv env
source env/bin/activate
pip install -r requirements.txt

# Node dependencies (for Tailwind)
npm install

# Apply migrations and start servers (two terminals)
python manage.py migrate
python manage.py runserver   # terminal 1
npm run dev                  # terminal 2 — watches templates and recompiles tailwind.css
```

The dev settings module (`stugov.settings.dev`) is the default — `manage.py` selects it automatically. `DEBUG=True`, `ALLOWED_HOSTS=["*"]`, and a random `SECRET_KEY` is generated on each startup if none is set in the environment.

## Production

Deployed as two Docker containers (Wagtail + nginx) via Docker Compose.

**Prerequisites:** Docker, a `.env` file at the repo root.

### Environment variables

| Variable | Required | Example |
|----------|----------|---------|
| `DJANGO_SETTINGS_MODULE` | yes | `stugov.settings.production` |
| `DJANGO_SECRET_KEY` | yes | (long random string) |
| `DJANGO_ALLOWED_HOSTS` | yes | `sg.rpi.edu` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | yes | `https://sg.rpi.edu` |
| `HOST_DATA_DIR` | yes | `/var/lib/stugov-site/` |
| `DJANGO_SECURE_SSL_REDIRECT` | no | `1` (enable after confirming proxy forwards `X-Forwarded-Proto: https`) |
| `DJANGO_HSTS_SECONDS` | no | `31536000` (enable after SSL redirect is confirmed) |

### First deploy

```bash
# On the server: make the data directory owned by the container user (UID 1002)
sudo mkdir -p /var/lib/stugov-site
sudo chown -R 1002:1002 /var/lib/stugov-site

# Copy the existing database into the data directory if migrating
cp db.sqlite3 /var/lib/stugov-site/

# Build and start
docker compose up -d --build
```

On startup the container automatically runs `collectstatic` then `migrate` before gunicorn starts.

### Subsequent deploys

```bash
docker compose up -d --build
```

### Static files

Static files are compiled into the image at build time:
- **Tailwind CSS** — compiled by a Node builder stage (`npm run build`) and baked into the image.
- **Other statics** — collected at container startup via `manage.py collectstatic` into a named Docker volume (`static_files`) shared with the nginx container.

### Nginx

nginx sits in front of Wagtail on port 80. TLS is expected to be terminated by an upstream proxy (load balancer or host-level reverse proxy) that sets `X-Forwarded-Proto: https`. nginx passes this header through to Django.

If your upstream proxy does not set `X-Forwarded-Proto`, Django will not recognise requests as secure and `DJANGO_SECURE_SSL_REDIRECT=1` will cause a redirect loop — verify the header is present before enabling it.
