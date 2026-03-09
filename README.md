# Event Processing System

Sistema de processamento de eventos construído em **Python**, utilizando **FastAPI**, **PostgreSQL**, **Docker** e **Kubernetes**.
O objetivo do projeto é demonstrar a construção de uma arquitetura baseada em eventos (Event-Driven Architecture) capaz de registrar e processar eventos de forma escalável.

---

# Arquitetura

O sistema segue uma abordagem simples de **Event Ingestion**, onde eventos são recebidos por uma API e persistidos em um banco de dados para posterior processamento.

Fluxo atual:

Client → API → PostgreSQL

1. Um cliente envia um evento para a API.
2. A API valida o payload.
3. O evento é persistido na tabela `events`.
4. O evento pode ser consumido posteriormente por workers ou serviços downstream.

---

# Tecnologias utilizadas

* Python 3.11
* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* Docker
* Kubernetes

---

# Estrutura do projeto

```
project-root
│
├── app
│   ├── api
│   │   └── events.py
│   │
│   ├── models
│   │   └── event.py
│   │
│   ├── schemas
│   │   └── event_schema.py
│   │
│   ├── services
│   │   └── event_service.py
│   │
│   ├── db
│   │   ├── base.py
│   │   └── session.py
│   │
│   └── main.py
│
├── alembic
│
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# Modelo de dados

Tabela `events`

| Campo      | Tipo      | Descrição               |
| ---------- | --------- | ----------------------- |
| id         | integer   | Identificador do evento |
| type       | string    | Tipo do evento          |
| payload    | json      | Dados do evento         |
| status     | string    | Estado do evento        |
| created_at | timestamp | Data de criação         |

---

# Executando com Docker

Subir o ambiente:

```
docker compose up --build
```

Executar migrations:

```
docker compose exec api alembic upgrade head
```

A API ficará disponível em:

```
http://localhost:8000
```

---

# Endpoint disponível

## Health Check

GET /health

Resposta:

```
{
  "status": "ok"
}
```

---

## Criar evento

POST /events

Payload:

```
{
  "type": "order_created",
  "payload": {
    "order_id": 123
  }
}
```

Resposta esperada:

```
{
  "id": 1,
  "type": "order_created",
  "payload": {
    "order_id": 123
  },
  "status": "pending"
}
```

---

# Executando no Kubernetes

1. Build da imagem

```
docker build -t event-processing-system .
```

2. Deploy no cluster

```
kubectl apply -f k8s/
```

3. Verificar pods

```
kubectl get pods
```

---

# Próximos passos do projeto

* Implementar sistema de **workers para processamento de eventos**
* Adicionar **fila de notificações**
* Implementar **retry e dead letter queue**
* Adicionar **observabilidade (logs e métricas)**

---

# Objetivo do projeto

Este projeto foi criado como exercício prático para estudar:

* Arquitetura orientada a eventos
* Orquestração com Kubernetes
* Integração entre serviços e banco de dados
* Boas práticas de estruturação de APIs em Python

---
