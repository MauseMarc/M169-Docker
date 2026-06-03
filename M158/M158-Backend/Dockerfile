FROM python:3.12.2-slim
ADD app/main.py .

WORKDIR /app
COPY app/ .

RUN pip install flask flask_cors mariadb

CMD ["python", "main.py"]