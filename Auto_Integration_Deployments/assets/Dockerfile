FROM python:3.10
COPY main.py /app/
WORKDIR /app/
RUN python3 -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "main.py"]
