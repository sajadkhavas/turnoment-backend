.PHONY: install lint check test ci infra-up infra-down

install:
	python -m pip install -U pip
	pip install -e '.[dev]'

lint:
	ruff check .

check:
	python -m compileall -q apps config manage.py
	python manage.py check --settings=config.settings.test
	python manage.py makemigrations --check --dry-run --settings=config.settings.test

test:
	pytest -q

ci: lint check test

infra-up:
	docker compose up -d postgres redis

infra-down:
	docker compose down
