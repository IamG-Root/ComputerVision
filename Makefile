# Variables.
VENV_NAME=cvenv
PYTHON=python
SERVER_DEPENDENCIES=requirements/server.txt
MODULE_DEPENDENCIES=requirements/module.txt
LOGS_DIR=logs
INSTALL_LOG=install.log

# Virtual environment creation\activation.
$(VENV_NAME)/bin/activate: 
	@echo "\033[1;33mCreating virtual environment...\033[0m"
	@$(PYTHON) -m venv $(VENV_NAME) --system-site-packages
	@echo "\033[0;32mCreated virtual environment.\033[0m"

# Module dependencies installation on virtual environment.
install_module: $(VENV_NAME)/bin/activate
	@echo "\033[1;33mInstalling dependencies...\033[0m"
	@mkdir -p $(LOGS_DIR)
	@$(VENV_NAME)/bin/pip install --upgrade pip > $(LOGS_DIR)/$(INSTALL_LOG) 2>&1
	@$(VENV_NAME)/bin/pip install -r $(MODULE_DEPENDENCIES) >> $(LOGS_DIR)/$(INSTALL_LOG) 2>&1
	@echo "\033[0;32mModule dependencies installed.\033[0m"

# Server dependencies installation on virtual environment.
install_server: $(VENV_NAME)/bin/activate
	@echo "\033[1;33mInstalling dependencies...\033[0m"
	@mkdir -p $(LOGS_DIR)
	@$(VENV_NAME)/bin/pip install --upgrade pip > $(LOGS_DIR)/$(INSTALL_LOG) 2>&1
	@$(VENV_NAME)/bin/pip install -r $(SERVER_DEPENDENCIES) >> $(LOGS_DIR)/$(INSTALL_LOG) 2>&1
	@echo "\033[0;32mServer dependencies installed.\033[0m"

# Numpy uninstall.
uninstall_numpy: $(VENV_NAME)/bin/activate
	@echo "\033[1;33mUninstalling numpy...\033[0m"
	@$(VENV_NAME)/bin/pip uninstall -y numpy >> $(LOGS_DIR)/$(INSTALL_LOG) 2>&1
	@echo "\033[0;32mUninstalled numpy.\033[0m"

# Giving execution permissions to launcher
mark_executable:
	@chmod +x launcher.sh
	@echo "\033[0;32m'launcher.sh' marked as executable.\033[0m"

# Exporting .pt models in ncnn format.
export_models: $(VENV_NAME)/bin/activate
	@echo "\033[1;33mExporting models in ncnn format...\033[0m"
	@mkdir -p $(LOGS_DIR)
	@for model in models/*.pt; do \
	echo "\033[1;33mExporting [$$model]\033[0m"; \
	$(VENV_NAME)/bin/python tools/export_ncnn.py "$$model" > "$(LOGS_DIR)/$$(basename "$$model" .pt).log" 2>&1 || exit $$?; \
	done
	@echo "\033[0;32mAll models exported in ncnn format.\033[0m"

# Module setup.
module: install_module uninstall_numpy mark_executable
	@echo "\033[0;32mModule setup completed.\033[0m"

# Server setup.
server: install_server uninstall_numpy mark_executable
	@echo "\033[0;32mServer setup completed.\033[0m"

# Import shared edge configuration, preserving parameters introduced by this version.
.PHONY: copy_config copy_config_module copy_config_server
copy_config: copy_config_module

copy_config_module copy_config_server: export COPY_CONFIG_SOURCE = $(value SOURCE)
copy_config_module:
	@$(PYTHON) tools/copy_config.py --destination module/config.py

copy_config_server:
	@$(PYTHON) tools/copy_config.py --destination server/config.py

# Removing virtual environment.
clean:
	@echo "\033[1;33mCleaning virtual environment...\033[0m"
	@rm -rf $(VENV_NAME)
	@rm -rf $(LOGS_DIR)
	@for model in models/*.onnx; do rm -rf $$model; done
	@for model in models/*_ncnn_model; do rm -rf $$model; done
	@echo "\033[0;32mRemoved virtual environment.\033[0m"
