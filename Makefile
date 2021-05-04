APP_BIN := .venv/bin/todo-server
PYTHON_BIN := .venv/bin/python
PIP_BIN := .venv/bin/pip
DOCKER := kfdm/todo-server

.PHONY:	test build migrate run shell clean pip reset dist
.DEFAULT: test

test: ${APP_BIN}
	${APP_BIN} test -v 2

$(PIP_BIN):
	python3 -m venv .venv
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
	${APP_BIN} makemigrations todo
	${APP_BIN} migrate
run: migrate
	${APP_BIN} runserver
shell: migrate
	${APP_BIN} shell

clean:
	rm -rf .venv
