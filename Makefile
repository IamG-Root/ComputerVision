# Variables.
VENV_NAME=cvenv
PYTHON=python
SERVER_DEPENDENCIES=paho-mqtt
MODULE_DEPENDENCIES=ultralytics ncnn paho-mqtt

# Virtual environment creation\activation.
$(VENV_NAME)/bin/activate: 
	@echo "\033[1;33mCreating virtual environment...\033[0m"
	$(PYTHON) -m venv $(VENV_NAME) --system-site-packages
	@echo "\033[0;32mCreated virtual environment.\033[0m"

# Module dependencies installation on virtual environment.
install_module: $(VENV_NAME)/bin/activate
	@echo "\033[1;33mInstalling dependencies...\033[0m"
	$(VENV_NAME)/bin/pip install --upgrade pip
	$(VENV_NAME)/bin/pip install $(MODULE_DEPENDENCIES)
	@echo "\033[0;32mModule dependencies installed.\033[0m"

# Server dependencies installation on virtual environment.
install_server: $(VENV_NAME)/bin/activate
	@echo "\033[1;33mInstalling dependencies...\033[0m"
	$(VENV_NAME)/bin/pip install --upgrade pip
	$(VENV_NAME)/bin/pip install $(SERVER_DEPENDENCIES)
	@echo "\033[0;32mServer dependencies installed.\033[0m"

# Numpy uninstall.
uninstall_numpy: $(VENV_NAME)/bin/activate
	@echo "\033[1;33mUninstalling numpy...\033[0m"
	$(VENV_NAME)/bin/pip uninstall -y numpy
	@echo "\033[0;32mUninstalled numpy.\033[0m"

# Exporting .pt models in ncnn format.
export_models: $(VENV_NAME)/bin/activate
	echo "\033[1;33mExporting models in ncnn format...\033[0m"
	for model in models/*.pt; do \
	$(VENV_NAME)/bin/yolo export model=$$model format=ncnn; \
	done

# Module setup.
module: install_module uninstall_numpy
	@echo "\033[0;32mModule setup completed.\033[0m"

# Server setup.
server: install_server uninstall_numpy
	@echo "\033[0;32mServer setup completed.\033[0m"

# Removing virtual environment.
clean:
	@echo "\033[1;33mCleaning virtual environment...\033[0m"
	rm -rf $(VENV_NAME)
	@echo "\033[0;32mRemoved virtual environment.\033[0m"
