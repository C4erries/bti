PYTHON ?= python
VENV ?= .venv

ifeq ($(OS),Windows_NT)
VENV_BIN := $(VENV)/Scripts
PYTHON_BIN := $(VENV_BIN)/python.exe
PIP := $(VENV_BIN)/pip.exe
else
VENV_BIN := $(VENV)/bin
PYTHON_BIN := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
endif

.PHONY: install run clean

install: $(VENV_BIN)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

$(VENV_BIN):
	$(PYTHON) -m venv $(VENV)

run: install
	$(PYTHON_BIN) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	$(PYTHON) -c "import shutil; shutil.rmtree('$(VENV)', ignore_errors=True)"
