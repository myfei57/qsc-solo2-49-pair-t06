FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY linecontrol ./linecontrol
COPY web ./web
COPY pyproject.toml ./

EXPOSE 8080

CMD ["python", "-m", "linecontrol", "--addr", ":8080", "--data", "/data", "--web", "/src/web"]
