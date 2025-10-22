# ComputerVision

This application is a modular Computer Vision system designed to detect objects from a camera feed and transmit real-time telemetry data.

It is divided into two main components:
- Module: captures frames from a camera, performs object detection, and sends telemetry data to the server via MQTT;
- Server: receives telemetry data from modules and processes it for analysis, monitoring, or integration with other systems.

## Installation

### Module

- Install virtual environment using `make module`;
- If not done yet, export your models in ncnn format using: `make export_models`;
- Setup your `config.py` file;
- Calibrate module using: `module/calibration.py`;

### Server

- Install virtual environment using `make server`;
- Setup your `server/config.py` file;

## Usage

### Module

- Launch using `cvenv/bin/python module/main.py` or `source cvenv/bin/activate; python module/main.py` and arguments:
    - `--debug` Print detection log messages;
    - `--draw` Display a window with the camera view;
- Stop execution with `Ctrl + C`.

### Server

- Launch using `cvenv/bin/python server/main.py` or `source cvenv/bin/activate; python server/main.py`.
- Stop execution with `Ctrl + C`