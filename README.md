# Smart IoT Devices Project
## Installation
Install `picamera2` Python module
```shell
sudo apt install python3-picamera2 --no-install-recommends
```
Add these settings to `/boot/config.txt` and reboot the RaspberryPi.
```ini
camera_auto_detect=0
dtoverlay=imx219
```
Create a Python virtual environment and install all dependencies
```shell
python3 -m venv siotd24 --system-site-packages
source siotd24/bin/activate
pip install --upgrade -r requirements.txt
```
Install and configure Blinka, needed by `adafruit-python-shell`, and reboot the RaspberryPi.

```shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py
```
## Configuration
Copy `.env.dist` to `.env` and add Telegram and InfluxDB connection parameters.

Start InfluxDB container:
```shell
docker compose up -d
```

Convert `YOLO11` model to NCNN format

```shell
source siotd24/bin/activate
python3 yolo2ncnn.py
```
## Usage
Run `Smart Temperature Monitor`:

```shell
source siotd24/bin/activate
python3 main.py
```

