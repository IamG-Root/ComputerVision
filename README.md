# ComputerVision

## Installation

### Module

- Install virtual environment using `make module`;
- Activate python virtual environment: `source cvenv\bin\activate`;
- If not done yet, export your model in ncnn format using: `yolo export model=mymodel.pt format=ncnn`
- Setup your `config.py` file;
- Launch using `python main.py` and arguments:
    - `--debug` Print detection log messages;
    - `--draw` Display debug window;
    - `--send` Send detections to server.

### Server

- Install virtual environment using `make server`;
- Activate python virtual environment: `source cvenv\bin\activate`;
- Launch using `python receiver.py`.