# smart-meter-influxdb-docker

A script to read a smart meter and send its data to InfluxDB

# Description

Description of smart meter (4.2.2)
https://www.netbeheernederland.nl/_upload/Files/Slimme_meter_15_32ffe3cc38.pdf

# How to use

How to run with docker and docker-compose
- include linking of dev/ttyUSB0
- Include log-directory

# Configuration
The following environment variables can be set.

| Variable name     | Description                                                            | Default   | Required? |
| ----------------- | ---------------------------------------------------------------------- | --------- | --------- |
| LOG_LEVEL         | The log level to use. Can be CRITICAL, ERROR, WARNING, INFO, OR DEBUG. | WARNING   |           |
| BAUD_RATE         | The baud rate of the serial device                                     | 115200    |           |
| INFLUXDB_HOST     | The hostname of the InfluxDB server                                    | localhost |           |
| INFLUXDB_PORT     | The port of the InfluxDB server                                        | 8086      |           |
| INFLUXDB_USER     | The username to connect to the InfluxDB server                         |           |           |
| INFLUXDB_PASSWORD | The password to connect to the InfluxDB server                         |           |           |
| INFLUXDB_DATABASE | The database name InfluxDB to send the data to                         |           | Required  |

# Developing?

`docker build --tag pythontest .`

`docker run -it --rm --device=/dev/ttyUSB0 pythontest:latest python`
