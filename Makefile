.PHONY: help build up down restart logs status test test-unit test-failover clean

help:
	@echo "DriftGuard Management Commands:"
	@echo "  make up            - Build and launch the DriftGuard stack in the background"
	@echo "  make down          - Gracefully stop all services"
	@echo "  make restart       - Restart the stack"
	@echo "  make build         - Rebuild Docker images without cache"
	@echo "  make logs          - Follow container logs (all services)"
	@echo "  make status        - Query Sentinel diagnostic status endpoint"
	@echo "  make test          - Run full integration & gateway verification test suite"
	@echo "  make test-unit     - Run Sentinel Python unit tests (pytest)"
	@echo "  make test-failover - Run automated failover and recovery exercise"
	@echo "  make clean         - Stop services and purge data volumes"

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build --no-cache

logs:
	docker compose logs -f --tail=100

status:
	@curl -s http://127.0.0.1:8000/status | jq . || curl -s http://127.0.0.1:8000/status

test:
	@./scripts/test_gateway.sh

test-unit:
	@docker compose exec sentinel pytest sentinel/tests/ -v || pytest sentinel/tests/ -v

test-failover:
	@./scripts/test_failover.sh

clean:
	docker compose down -v
