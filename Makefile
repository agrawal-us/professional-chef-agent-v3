dev:
	@docker-compose up

stop:
	@docker-compose down

build:
	@docker-compose build

logs:
	@docker-compose logs -f api

reset:
	@docker-compose down -v
	@docker-compose up -d

migrate:
	@docker-compose exec api alembic upgrade head

migrate-down:
	@docker-compose exec api alembic downgrade -1

db-shell:
	@docker-compose exec postgres psql -U chef -d chef_agent

db-tables:
	@docker-compose exec postgres psql -U chef -d chef_agent \
	  -c "\dt" -c "\d sessions" -c "\d detection_logs"

.PHONY: dev stop build logs reset migrate migrate-down db-shell db-tables
