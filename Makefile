SYSTEM_PYTHON ?= python3.10
ENV_DIR := .venv
APP_BIN := $(ENV_DIR)/bin/todo-server
PYTHON_BIN := $(ENV_DIR)/bin/python
PIP_BIN := $(ENV_DIR)/bin/pip
DOCKER := kfdm/todo-server

.PHONY:	test build migrate run shell clean pip reset dist
.DEFAULT: test

test: ${APP_BIN}
	${APP_BIN} test -v 2

$(PIP_BIN):
	$(SYSTEM_PYTHON) -m venv $(ENV_DIR)
	$(PIP_BIN) install -U pip

${APP_BIN}: $(PIP_BIN)
	${PIP_BIN} install -r docker/requirements.txt
	${PIP_BIN} install -e .[dev,standalone]
pip: ${APP_BIN}
	${PIP_BIN} install -r docker/requirements.txt
	${PIP_BIN} install -e .[dev,standalone]

build:
	docker build . --tag ${DOCKER}:local
dist:
	${PYTHON_BIN} bdist_wheel
reset: ${APP_BIN}
	${APP_BIN} migrate todo zero
migrate: ${APP_BIN}
	${APP_BIN} migrate
run: migrate
	${APP_BIN} runserver 5232
shell: migrate
	${APP_BIN} shell

clean:
	rm -rf .venv
