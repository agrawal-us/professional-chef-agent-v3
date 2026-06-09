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

.PHONY: dev stop build logs reset
