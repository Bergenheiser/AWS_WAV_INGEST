init:
	sudo su -
	python3 -m venv .venv
	source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	localstack start -d

format:
	isort code/*
	black code/*