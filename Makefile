.PHONY: build workers stop

WORKERS ?= 1

docker-build:
	docker compose down -v
	docker compose up --build --scale worker=$(WORKERS)

workers:
	docker compose up --scale worker=$(WORKERS)

stop:
	docker compose down


# =========================
# CONFIG (DEFAULTS)
# =========================
APP_NAME ?= proccessment-events-system
IMAGE_TAG ?= 1.0
IMAGE_NAME ?= $(APP_NAME):$(IMAGE_TAG)

K8S_DIR ?= ./k8s
DEPLOYMENT_FILE ?= $(K8S_DIR)/deployment.yaml
SERVICE_FILE ?= $(K8S_DIR)/service.yaml

NAMESPACE ?= default

# =========================
# HELP
# =========================
.PHONY: help
help:
	@echo "📖 Comandos disponíveis:"
	@echo "make build              -> Build da imagem"
	@echo "make deploy             -> Apply no Kubernetes"
	@echo "make up                 -> Build + Deploy"
	@echo "make restart            -> Restart do deployment"
	@echo "make clean              -> Remover recursos"

# =========================
# BUILD IMAGE (MINIKUBE)
# =========================
.PHONY: build
build:
	@echo "🐳 Buildando imagem $(IMAGE_NAME)..."
	eval $$(minikube docker-env) && docker build -t $(IMAGE_NAME) .

# =========================
# DEPLOY
# =========================
.PHONY: deploy
deploy:
	@echo "🚀 Aplicando manifests..."
	kubectl apply -f $(DEPLOYMENT_FILE) -n $(NAMESPACE)
	kubectl apply -f $(SERVICE_FILE) -n $(NAMESPACE)

# =========================
# FULL PIPELINE
# =========================
.PHONY: up
up: build deploy
	@echo "✅ Deploy finalizado!"

# =========================
# RESTART
# =========================
.PHONY: restart
restart:
	kubectl rollout restart deployment $(APP_NAME) -n $(NAMESPACE)

# =========================
# DELETE
# =========================
.PHONY: clean
clean:
	@echo "🧹 Removendo recursos..."
	kubectl delete -f $(DEPLOYMENT_FILE) -n $(NAMESPACE) || true
	kubectl delete -f $(SERVICE_FILE) -n $(NAMESPACE) || true