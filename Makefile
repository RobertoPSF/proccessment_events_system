.PHONY: build workers stop

WORKERS ?= 1

build:
	docker compose down -v
	docker compose up --build --scale worker=$(WORKERS)

workers:
	docker compose up --scale worker=$(WORKERS)

stop:
	docker compose down