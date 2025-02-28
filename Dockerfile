FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9
COPY . /app
RUN pip install --upgrade pip
COPY requirements-server.txt .
RUN pip install -r requirements-server.txt

EXPOSE 8000


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
