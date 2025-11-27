VENV ?= .venv

ifeq ($(OS),Windows_NT)
PYTHON_LAUNCH ?= py -3.12
VENV_BIN := $(VENV)/Scripts
PYTHON_BIN := $(VENV_BIN)/python.exe
PIP := $(VENV_BIN)/pip.exe
else
PYTHON_LAUNCH ?= python3.12
VENV_BIN := $(VENV)/bin
PYTHON_BIN := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
endif

.PHONY: install run clean

install: $(VENV_BIN)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

$(VENV_BIN):
	$(PYTHON_LAUNCH) -m venv $(VENV)

run:
	$(PYTHON_BIN) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	$(PYTHON_LAUNCH) -c "import shutil; shutil.rmtree('$(VENV)', ignore_errors=True)"
