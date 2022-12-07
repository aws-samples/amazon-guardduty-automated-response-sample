.PHONY: setup build deploy format clean

setup:
	python3 -m venv .venv
	.venv/bin/python3 -m pip install -U pip wheel
	.venv/bin/python3 -m pip install -r requirements-dev.txt
	.venv/bin/python3 -m pip install -r src/requirements.txt
	.venv/bin/pre-commit install

build:
	sam build

deploy:
	sam deploy

clean:
	sam delete

format:
	.venv/bin/black .
