.PHONY: install run docker-build docker-up docker-down test

install:
	pip install --upgrade pip
	pip install -r requirements.txt

run:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t senseable-backend .

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

test:
	pytest
