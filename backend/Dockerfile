FROM python:3.12-slim
WORKDIR /srv
# Pinned dependency set first: it is the layer that should stay cached, and it
# makes the image reproducible instead of resolving whatever is newest today.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
# --no-deps: everything the project needs is already pinned above.
RUN pip install --no-cache-dir --no-deps .
ENV PYTHONPATH=/srv
EXPOSE 8000
# --proxy-headers/--forwarded-allow-ips trust X-Forwarded-For from the compose
# network so per-IP login rate limiting sees real client IPs, not the web
# container's; the api port is never published, only web can reach it.
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
