import os
import sys
import serial
import logging
import json
from influxdb import InfluxDBClient
import paho.mqtt.client as mqtt

# Main method and loop
def main():
  init_logger()
  logging.info('Smart meter logging started')

  serial_client = open_serial_client()
  influxdb_client = open_influxdb_client()
  mqtt_client = open_mqtt_client()

  while True:
    message = get_next_message(serial_client)
    data = convert_message_to_data(message)
    # send_data_to_influxdb(influxdb_client, data)
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

# Opens the InfluxDB Client
def open_influxdb_client():
  host = os.environ.get('INFLUXDB_HOST') or 'localhost'
  port = int(os.environ.get('INFLUXDB_PORT') or '8086')
  user = os.environ.get('INFLUXDB_USER') or ''
  password = os.environ.get('INFLUXDB_PASSWORD') or ''
  database = os.environ.get('INFLUXDB_DATABASE')

  if database == None:
    logging.critical('No database set, use environment variable INFLUXDB_DATABASE to set it.')
    sys.exit('No database set, use environment variable INFLUXDB_DATABASE to set it.')

  try:
    client = InfluxDBClient('192.168.2.4', 8086, '', '', 'energy')
    return client
  except err:
    logging.critical(f'Cannot open InfluxDB Client: {err}')
    sys.exit(f'Cannot open InfluxDB Client: {err}')

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
      data['timestamp'] = time_string
      logging.info(f'Timestamp - {time_string}')

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

  data['meter_total_tariff'] = data['meter_low_tariff'] + data['meter_normal_tariff']
  data['meter_supplied_total_tariff'] = data['meter_supplied_low_tariff'] + data['meter_supplied_normal_tariff']
  return data

# Sends the data to InfluxDB
def send_data_to_influxdb(client, data):
  influx_data = [
    {
      "measurement": "smart_meter",
      "time": data['timestamp'],
      "fields": data
    }
  ]
  client.write_points(influx_data)
  logging.info('Data send to InfluxDB')

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
