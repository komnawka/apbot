FROM python:3.9-slim

RUN mkdir -p /usr/src/apbot/
WORKDIR /usr/src/apbot/

COPY . /usr/src/apbot/ 
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "apbot.py"]
