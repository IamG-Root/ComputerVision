# Variables.

VENV_NAME=cvenv
PYTHON=python
PIP=pip

# Virtual environment creation\activation.

$(VENV_NAME)/bin/activate: 
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_NAME) --system-site-packages
	@echo "Created virtual environment."

# Dependencies installation on virtual environment.

install: $(VENV_NAME)/bin/activate
	@echo "Installing dependencies..."
	$(VENV_NAME)/bin/pip install --upgrade pip
	$(VENV_NAME)/bin/pip install ultralytics ncnn paho-mqtt
	@echo "Dependencies installed."

# Numpy uninstall.

uninstall_numpy: $(VENV_NAME)/bin/activate
	@echo "Uninstalling numpy..."
	$(VENV_NAME)/bin/pip uninstall -y numpy
	@echo "Uninstalled numpy."

# Main setup.

setup: install uninstall_numpy
	@echo "Setup completed."

# Removing virtual environment.

clean:
	@echo "Cleaning virtual environment..."
	rm -rf $(VENV_NAME)
	@echo "Removed virtual environment."
