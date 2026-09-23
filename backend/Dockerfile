FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/srv
EXPOSE 8000
# --proxy-headers/--forwarded-allow-ips trust X-Forwarded-For from the compose
# network so per-IP login rate limiting sees real client IPs, not the web
# container's; the api port is never published, only web can reach it.
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
