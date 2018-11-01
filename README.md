# smart-meter-influxdb-docker

A script to read a smart meter and send its data to InfluxDB

# Description
This script connects to a smart meter that follows the DSMR standard. This tool was specifically written for version 4.2.2 (See the [manual](https://www.netbeheernederland.nl/_upload/Files/Slimme_meter_15_32ffe3cc38.pdf)), but it should either work for other versions too or only needs slight modifications.

# How to use
The script is packaged as a Docker container, so it needs Docker to run. You can either use Docker directly:

`docker run -it --rm --device=/dev/ttyUSB0 -e INFLUXDB_DATABASE='my-data' -v ./log:/var/log marktermaat/smart-meter-influxdb:latest python`

Or use the example docker-compose file and run:

`docker-compose up -d`

Keep in mind that log files are put (inside the Docker container) in /var/log, so if you want to see those log files you should bind that directory to one on the host machine.

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

# Development

- `docker build --tag marktermaat/smart-meter-influxdb .`
- `docker push marktermaat/smart-meter-influxdb`