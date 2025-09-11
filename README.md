# ComputerVision

## Installation

### Module

- Install virtual environment using `make module`;
- Activate python virtual environment: `source cvenv\bin\activate`;
- If not done yet, export your model in ncnn format using: `yolo export model=mymodel.pt format=ncnn`
- Calibrate module using: `module/calibration.py`
- Setup your `config.py` file;
- Launch using `python module/main.py` and arguments:
    - `--debug` Print detection log messages;
    - `--draw` Display debug window;
    - `--send` Send detections to server.

### Server

- Install virtual environment using `make server`;
- Activate python virtual environment: `source cvenv\bin\activate`;
- Setup your `server/config.py` file;
- Launch using `python server/main.py`.