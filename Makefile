# Configuration
TTY_PATH := /dev/ttyACM0
RSHELL_OPTS := --quiet

# MicroPython firmware
MPY_FIRMWARE_FILENAME := esp32c3-20230426-v1.20.0.bin
MPY_FIRMWARE_URL := https://micropython.org/resources/firmware/$(MPY_FIRMWARE_FILENAME)

# Helper variables
ACTIVATE_VENV := source venv/bin/activate

# Default target (deploys code)
all: deploy

# -- Dev environment

# Create venv and install dependencies
.PHONY: install-venv
install-venv:
	python3 -m venv venv
	$(ACTIVATE_VENV) && pip install -r requirements.txt

# -- Deployment

# Soft-reset (restart) the board
.PHONY: reset-board
reset-board:
	$(ACTIVATE_VENV) && rshell $(RSHELL_OPTS) -p $(TTY_PATH) repl "~ import machine ~ machine.soft_reset() ~"

# Copy all .py files from src/ (the default app) to the board
.PHONY: deploy
deploy:
	$(ACTIVATE_VENV) && rshell $(RSHELL_OPTS) -p $(TTY_PATH) cp -r "src/*" /pyboard

# Copy the default app from src/ to the board and restart the board (this will monitor the output of the code)
.PHONY: run
run: deploy reset-board

# -- Firmware flashing

# Download the MicroPython firmware to the downloads directory (if it does not exist yet)
.PHONY: download-firmware
download-firmware: downloads/$(MPY_FIRMWARE_FILENAME)

# Actually downloads the firmware
downloads/$(MPY_FIRMWARE_FILENAME):
	@mkdir -p downloads/
	@if ! which wget >/dev/null 2>&1; then \
		echo "ERROR: wget is not installed! Please install wget first."; \
		echo; \
		echo "Alternatively, download the MicroPython firmware manually from the following URL into the \"downloads\" directory," \
			"and then rerun this command:"; \
		echo "$(MPY_FIRMWARE_URL)"; \
		echo; \
		exit 1; \
	fi
	wget -O "downloads/$(MPY_FIRMWARE_FILENAME)" "$(MPY_FIRMWARE_URL)"

# Flash the firmware to the ESP32 (automatically downloads the firmware first)
.PHONY: flash-firmware
flash-firmware: download-firmware
	$(ACTIVATE_VENV) && esptool.py --chip esp32c3 --port $(TTY_PATH) erase_flash
	$(ACTIVATE_VENV) && esptool.py --chip esp32c3 --port $(TTY_PATH) --baud 460800 write_flash -z 0x0 downloads/$(MPY_FIRMWARE_FILENAME)
	@echo
	@echo "MicroPython has been flashed to the board!"

# -- Others

# Include local Makefile if it exists (use this file to override variables etc.)
-include Makefile.local
