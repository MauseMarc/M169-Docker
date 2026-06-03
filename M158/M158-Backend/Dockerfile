FROM python:3.12.2-slim

WORKDIR /app
COPY app/ .

RUN pip install flask flask_cors pymysql

CMD ["python", "main.py"]