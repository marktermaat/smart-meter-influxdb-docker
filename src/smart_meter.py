import os
import sys
import serial
import logging
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import pytz

# Main method and loop
def main():
  init_logger()
  logging.info('Smart meter logging started')

  serial_client = open_serial_client()
  mqtt_client = open_mqtt_client()

  while True:
    message = get_next_message(serial_client)
    data = convert_message_to_data(message)
    send_data_to_mqtt(mqtt_client, data)

# Initializes the logger
def init_logger():
  log_level_str = os.environ.get('LOG_LEVEL') or 'WARNING'
  log_level = getattr(logging, log_level_str)
  logging.basicConfig(filename='/var/log/smart_meter.log', level=log_level)

# Opens the serial device client
def open_serial_client():
  baud_rate_str = os.environ.get('BAUD_RATE') or '115200'
  baud_rate = int(baud_rate_str)

  ser = serial.Serial()
  ser.baudrate = baud_rate
  ser.bytesize=serial.SEVENBITS
  ser.parity=serial.PARITY_EVEN
  ser.stopbits=serial.STOPBITS_ONE
  ser.xonxoff=0
  ser.rtscts=0
  ser.timeout=20
  ser.port="/dev/ttyUSB0"

  try:
    ser.open()
  except err:
    logging.critical(f'Cannot open serial device: {err}')
    sys.exit(f'Cannot open serial device: {err}')

  return ser

# Reads the next message from the serial device
def get_next_message(ser):
  line_counter = 0
  lines = []

  while line_counter < 36:
    try:
      line_raw = ser.readline()
    except error:
      logging.error(f'Cannot read from serial device: {error}')

    line = str(line_raw, 'utf-8').strip()

    # If a line containing 'ZIV-METER' is found, reset the line_counter to 0.
    # This is a fail-safe if the program happens to start in the middle of a message.
    if "ZIV-METER" in line: line_counter = 0

    lines.append(line)
    line_counter += 1

  return lines

# Converts the serial message to a dictionary, reading the useful datapoints from it.
def convert_message_to_data(message):
  data = {}
  for line in message:
   # Time
    if line.startswith('0-0:1.0.0'):
      logging.info(f'Line: {line}')
      t = line[10:22]
      time_string = f'20{t[0:2]}-{t[2:4]}-{t[4:6]}T{t[6:8]}:{t[8:10]}:{t[10:12]}Z'
      tz = pytz.timezone("Europe/Amsterdam")
      naive = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%SZ')
      local_timestamp = tz.localize(naive)
      utc_timestamp = local_timestamp.astimezone(pytz.utc).isoformat()
      data['timestamp'] = utc_timestamp
      logging.info(f'Timestamp - {utc_timestamp}')

    # Energy meter low tariff
    if line.startswith('1-0:1.8.1'):
      logging.info(f'Line: {line}')
      usage_str = line[10:20]
      usage = float(usage_str)
      data['meter_low_tariff'] = usage
      logging.info(f'Meter - low tariff: {usage}')

    # Energy meter normal tariff
    if line.startswith('1-0:1.8.2'):
      logging.info(f'Line: {line}')
      usage_str = line[10:20]
      usage = float(usage_str)
      data['meter_normal_tariff'] = usage
      logging.info(f'Meter - normal tariff: {usage}')

    # Current energy usage
    if line.startswith('1-0:1.7.0'):
      logging.info(f'Line: {line}')
      usage_str = line[10:16]
      usage = float(usage_str)
      data['current_energy_usage'] = usage
      logging.info(f'Current usage - energy: {usage}')

    # Energy meter supplied low tariff
    if line.startswith('1-0:2.8.1'):
      logging.info(f'Line: {line}')
      usage_str = line[10:20]
      usage = float(usage_str)
      data['meter_supplied_low_tariff'] = usage
      logging.info(f'Meter supplied - low tariff: {usage}')

    # Energy meter supplied normal tariff
    if line.startswith('1-0:2.8.2'):
      logging.info(f'Line: {line}')
      usage_str = line[10:20]
      usage = float(usage_str)
      data['meter_supplied_normal_tariff'] = usage
      logging.info(f'Meter supplied - normal tariff: {usage}')

    # Current energy supplied
    if line.startswith('1-0:2.7.0'):
      logging.info(f'Line: {line}')
      usage_str = line[10:16]
      usage = float(usage_str)
      data['current_energy_supplied'] = usage
      logging.info(f'Current supplied - energy: {usage}')

    # Current gas usage
    if line.startswith('0-1:24.2.1'):
      logging.info(f'Line: {line}')
      usage_str = line[26:35]
      usage = float(usage_str)
      data['current_gas_usage'] = usage
      logging.info(f'Current usage - gas: {usage}')

    # Current voltage phase 1 (L1)
    if line.startswith('1-0:32.7.0'):
      logging.info(f'Line: {line}')
      usage_str = line[11:16]
      usage = float(usage_str)
      data['voltage_l1'] = usage
      logging.info(f'Current voltage - phase 1: {usage}')

    # Current voltage phase 2 (L2)
    if line.startswith('1-0:52.7.0'):
      logging.info(f'Line: {line}')
      usage_str = line[11:16]
      usage = float(usage_str)
      data['voltage_l2'] = usage
      logging.info(f'Current voltage - phase 2 {usage}')

    # Current voltage phase 3 (L3)
    if line.startswith('1-0:72.7.0'):
      logging.info(f'Line: {line}')
      usage_str = line[11:16]
      usage = float(usage_str)
      data['voltage_l3'] = usage
      logging.info(f'Current voltage - phase 3: {usage}')

  data['meter_total_tariff'] = data['meter_low_tariff'] + data['meter_normal_tariff']
  data['meter_supplied_total_tariff'] = data['meter_supplied_low_tariff'] + data['meter_supplied_normal_tariff']
  return data

def open_mqtt_client():
  host = os.environ.get('MQTT_HOST') or 'localhost'
  port = os.environ.get("MQTT_PORT") or 1883

  client = mqtt.Client(client_id="smart-meter")
  client.connect(host, port, 60)
  client.loop_start()
  return client

def send_data_to_mqtt(client, data):
  data_json = json.dumps(data)
  client.publish("data/smartmeter", payload=data_json, qos=1)

main()
