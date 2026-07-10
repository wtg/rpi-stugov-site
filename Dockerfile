# Use an official Python runtime based on Debian 12 "bookworm" as a parent image.
FROM python:3.12-slim-bookworm

# Add user that will be used in the container.
RUN useradd wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. Set PORT variable that is used by Gunicorn. This should match "EXPOSE"
#    command.
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet && apt-get install --yes --quiet --no-install-recommends \
    build-essential \
    libpq-dev \
    libmariadb-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libwebp-dev \
 && rm -rf /var/lib/apt/lists/*

# Install the application server.
RUN pip install "gunicorn>=21.2"

# Install the project requirements.
COPY requirements.txt /
RUN pip install -r /requirements.txt
RUN pip install setuptools

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Use /data folder for persistent data
RUN mkdir -p data static

# Recursively chown /app so the wagtail user owns both data/ and static/ —
# Docker initialises an empty named volume from the image directory's ownership,
# so static/ must be wagtail-owned here for collectstatic to succeed at runtime.
RUN chown -R wagtail:wagtail /app

# Copy the source code of the project into the container.
COPY --chown=wagtail:wagtail . .

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Runtime command: collect statics (needs SECRET_KEY from env for ManifestStaticFilesStorage),
# migrate, then start gunicorn bound on all interfaces so nginx can reach it.
CMD set -xe; \
    python manage.py collectstatic --noinput --clear; \
    python manage.py migrate --noinput; \
    gunicorn stugov.wsgi:application \
        --bind 0.0.0.0:${PORT} \
        --workers 1 \
        --timeout 120 \
        --access-logfile -
