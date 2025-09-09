# ComputerVision

## Installation

### Module

- Create python virtual environment: `python -m venv cvenv`;
- Activate python virtual environment: `source cvenv\bin\activate`;
- Install dependencies: ultralytics, paho-mqtt and any requested;
- Setup your `config.py` file;
- Launch with `python main.py` and arguments:
    - `--debug` Print detection log messages;
    - `--draw` Display debug window;
    - `--send` Send detections to server.