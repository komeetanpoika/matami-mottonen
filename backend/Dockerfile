FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install --no-cache-dir .
ENV PYTHONPATH=/srv
EXPOSE 8000
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000
