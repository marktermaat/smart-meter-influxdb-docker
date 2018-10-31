import os
import sys
import serial
import logging
from datetime import datetime
from influxdb import InfluxDBClient

# Main method and loop
def main():
  init_logger()
  logging.info('Smart meter logging started')

  serial_client = open_serial_client()
  influxdb_client = open_influxdb_client()

  while True:
    message = get_next_message(serial_client)
    data = convert_message_to_data(message)
    send_data_to_influxdb(influxdb_client, data)

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

  while line_counter < 26:
    try:
      line_raw = ser.readline()
    except error:
      logging.error(f'Cannot read from serial device: {error}')

    line = str(line_raw, 'utf-8').strip()

    # If a line containing 'KAIFA' is found, reset the line_counter to 0.
    # This is a fail-safe if the program happens to start in the middle of a message.
    if "\\" in line: line_counter = 0

    lines.append(line)
    line_counter += 1

  return lines

# Converts the serial message to a dictionary, reading the useful datapoints from it.
def convert_message_to_data(message):
  data = {}
  for line in message:

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

    # Current gas usage
    if line.startswith('0-1:24.2.1'):
      logging.info(f'Line: {line}')
      usage_str = line[26:35]
      usage = float(usage_str)
      data['current_gas_usage'] = usage
      logging.info(f'Current usage - gas: {usage}')

  data['meter_total_tariff'] = data['meter_low_tariff'] + data['meter_normal_tariff']
  return data

# Sends the data to InfluxDB
def send_data_to_influxdb(client, data):
  influx_data = [
    {
      "measurement": "smart_meter",
      "time": datetime.utcnow().isoformat(),
      "fields": data
    }
  ]
  client.write_points(influx_data)
  logging.info('Data send to InfluxDB')

main()