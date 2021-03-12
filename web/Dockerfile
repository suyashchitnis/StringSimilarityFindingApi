FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python -m spacy download en en_core_web_sm-2.0.0
CMD ["python","app.py"]
