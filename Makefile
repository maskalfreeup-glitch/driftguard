.PHONY: all build up down restart logs status test test-unit test-failover test-chaos clean help

all: up

build:
	docker compose build --no-cache

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=100

test:
	@chmod +x scripts/test_failover.sh
	@./scripts/test_failover.sh

test-failover: test

test-chaos:
	docker compose -f deploy/docker-compose.test.yml up -d --build
	sleep 3
	python3 tests/chaos/runner.py
	docker compose -f deploy/docker-compose.test.yml down -v

test-unit:
	@docker compose exec -e PYTHONPATH=/app sentinel pytest sentinel/tests/ -v || PYTHONPATH=. pytest sentinel/tests/ -v

test-gateway:
	@chmod +x scripts/test_gateway.sh
	@./scripts/test_gateway.sh

status:
	@curl -s http://127.0.0.1:8000/status | jq . 2>/dev/null || curl -s http://127.0.0.1:8000/status

clean:
	docker compose down -v --remove-orphans

help:
	@echo "DriftGuard Management Commands:"
	@echo "  make up            - Build and launch the DriftGuard stack in the background"
	@echo "  make down          - Gracefully stop all services"
	@echo "  make build         - Rebuild Docker images without cache"
	@echo "  make logs          - Follow container logs (all services)"
	@echo "  make test          - Run automated failover verification drill (scripts/test_failover.sh)"
	@echo "  make test-unit     - Run Sentinel Python unit tests (pytest)"
	@echo "  make status        - Query Sentinel diagnostic status endpoint"
	@echo "  make clean         - Stop services and purge data volumes"
