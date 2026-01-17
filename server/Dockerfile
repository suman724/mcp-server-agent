FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY . /app
RUN python -m pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "mcp_calculator"]
