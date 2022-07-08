.PHONY: setup build deploy format clean

setup:
	python3 -m venv .venv
	.venv/bin/python3 -m pip install -U pip wheel
	.venv/bin/python3 -m pip install -r requirements-dev.txt
	.venv/bin/python3 -m pip install -r src/requirements.txt

build:
	sam build

deploy:
	sam deploy

clean:
	sam delete

format:
	.venv/bin/black -t py39 --line-length 100 .
