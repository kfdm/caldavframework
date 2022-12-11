PKG_NAME = caldav_framework
CLI_NAME = todo-server
DOCKER_NAME = kfdm/todo-server
PKG_OPTS = .[standalone,dev]

SYSTEM_PYTHON ?= python3.7
VENV_PATH := .venv
APP_BIN := $(VENV_PATH)/bin/$(CLI_NAME)
PIP_BIN := $(VENV_PATH)/bin/pip

# Help 'function' taken from
# https://gist.github.com/prwhite/8168133#gistcomment-2278355
lessopts="--tabs=4 --quit-if-one-screen --RAW-CONTROL-CHARS --no-init"

# COLORS
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

TARGET_MAX_CHAR_NUM=20
.PHONY:	help
## Show help
help:
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk '/^[\%a-zA-Z\-\_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "  ${YELLOW}%-$(TARGET_MAX_CHAR_NUM)s${RESET} ${GREEN}%s${RESET}\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)


###############################################################################
### Pip Tasks
###############################################################################
PIPDEPTREE := $(VENV_PATH)/bin/pipdeptree
PIP_COMPILE := $(VENV_PATH)/bin/pip-compile

$(PIP_BIN):
	$(SYSTEM_PYTHON) -m venv $(VENV_PATH)

$(APP_BIN): $(PIP_BIN)
	$(PIP_BIN) install -r docker/requirements.txt -e $(PKG_OPTS)

.PHONY: pip
## Pip: Reinstall into our virtual env
pip:	$(PIP_BIN)
	$(PIP_BIN) install --upgrade pip setuptools wheel
	$(PIP_BIN) install -r docker/requirements.txt -e $(PKG_OPTS)

.PHONY: outdated
## Pip: Show outdated dependencies
outdated:	$(PIP_BIN)
	$(PIP_BIN) list --outdated

$(PIPDEPTREE): $(PIP_BIN)
	$(PIP_BIN) install pipdeptree

.PHONY: deps
## Pip: Show dependencies for our package
deps:	$(PIPDEPTREE)
	$(PIPDEPTREE) -p $(PKG_NAME)

$(PIP_COMPILE): $(PIP_BIN)
	$(PIP_BIN) install pip-tools

docker/requirements.txt: $(PIP_COMPILE) setup.py setup.cfg docker/requirements.in 
	$(PIP_COMPILE) --extra=standalone --output-file docker/requirements.txt setup.py docker/requirements.in --no-emit-index-url

.PHONY: compile
## Pip: Compile requirements
compile: docker/requirements.txt


###############################################################################
### Docker Tasks
###############################################################################

.PHONY:	build
## Docker: Build docker container
build:	docker/requirements.txt
	docker build . --tag test

###############################################################################
### Django Tasks
###############################################################################

.PHONY: web
## Django: Launch runserver for testing
web:	$(APP_BIN)
	$(APP_BIN) runserver 9000

.PHONY:	shell
## Django: Open Python shell
shell:	$(APP_BIN)
	$(APP_BIN) shell

.PHONY:	test
## Django: Run tests
test: $(APP_BIN)
	$(APP_BIN) test -v2
