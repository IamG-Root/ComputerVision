# ComputerVision

This application is a modular Computer Vision system designed to detect objects from a camera feed and transmit real-time telemetry data.

It is divided into two main components:
- **Module**: captures frames from a camera, performs object detection, and sends telemetry data to the server via MQTT;
- **Server**: receives telemetry data from modules and processes it for analysis, monitoring, or integration with other systems.

## Installation

### Module

- Install virtual environment using `make module`;
- If not done yet, export your models in ncnn format using: `make export_models`;
- Setup your `config.py` file;
- Calibrate module using: `module/calibration.py`.
- Mark the zones to exclude using `module/zones_editor.py`.

### Server

- Install virtual environment using `make server`;
- Setup your `server/config.py` file.

## Usage

### Module

- Launch using `cvenv/bin/python module/main.py` or `source cvenv/bin/activate; python module/main.py` or `./launcher.sh module` and arguments:
    - `--debug` Print detection log messages;
    - `--draw` Display a window with the camera view.
- Stop execution with `Ctrl + C`.

### Server

- Launch using `cvenv/bin/python server/main.py` or `source cvenv/bin/activate; python server/main.py` or `./launcher.sh server` and arguments:
    - `--debug` Print frame log messages;
    - `--draw` Display a window with the entities displayed in a graphical interface.
- Stop execution with `Ctrl + C`.

## Setup start on boot

- Create a new crontab using `sudo crontab -e`.
- Add `@reboot` + `bash` + `path-to-repository/launcher.sh` + argument `module` or `server`.
- Note that `--draw` arguments will not work beacause crontab starts before the graphical server.