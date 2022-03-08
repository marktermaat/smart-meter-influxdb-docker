FROM python:3.6-alpine
RUN pip install pyserial paho-mqtt pytz

COPY src/ /app
WORKDIR /app

CMD [ "python", "/app/smart_meter.py" ]