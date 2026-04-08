# 📦 Processment Events System

Um sistema **orientado a eventos** construído com padrões de produção para explorar desafios reais de backend. Este projeto implementa uma arquitetura robusta de processamento de eventos com persistência em banco de dados, workers concorrentes, idempotência e rate limiting.

---

## 🎯 Objetivo

Este é um projeto de estudo que demonstra:
- ✅ Arquitetura orientada a eventos
- ✅ Fila persistente em banco de dados relacional
- ✅ Workers concorrentes com travamento pessimista
- ✅ Idempotência e deduplicação
- ✅ Rate limiting
- ✅ Retry automático com timeout
- ✅ Padrões de produção (transações, índices, etc)

---

## 🏗️ Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────┐
│                CLIENTE/API                          │
│          (POST /events - POST /counter)             │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │    FastAPI Server      │
        │   (Port 8000)          │
        └────────┬───────────────┘
                 │
         ┌───────┴────────┐
         ▼                ▼
     ┌─────────┐    ┌──────────────┐
     │ Routes  │    │  Services    │
     │         │    │              │
     │ /events │    │EventService  │
     │/counter │    │Notification  │
     │/health  │    │FanOutService │
     └────┬────┘    └──────┬───────┘
          │                │
          └────────┬───────┘
                   ▼
        ┌──────────────────────┐
        │   PostgreSQL (BD)    │
        │                      │
        │ - Events            │
        │ - Notifications     │
        │ - Counters          │
        │ - FailedNotifications
        └──────────┬───────────┘
                 ▼
        ┌──────────────────────┐
        │   Worker Process     │
        │  (Processamento)     │
        │                      │
        │ • Fetch (SKIP LOCKED)│
        │ • Lock               │
        │ • Process            │
        │ • Rate Limiter       │
        │ • Retry              │
        └──────────────────────┘
```

---

## 🧠 Componentes Principais

### 1. **API (FastAPI)**
- Recebe eventos via HTTP
- Persiste eventos idempotentes
- Gera notificações via FanOut
- Incrementa contadores de usuários
- Health check

### 2. **Banco de Dados (PostgreSQL)**
- Armazena eventos com chave de idempotência
- Fila de notificações persistente
- Contadores de notificações por usuário
- Log de notificações falhas
- Índices otimizados para queries

### 3. **Worker (Background Process)**
- Processa notificações em lotes
- Travamento pessimista com `SKIP LOCKED`
- Retry automático com timeout
- Rate limiting configurável
- Tratamento de falhas

### 4. **FanOut Service**
- Expande um evento em múltiplas notificações
- Mapeia tipos de eventos para destinos
- Suporta múltiplos canais (email, audit log, analytics)

---

## 📊 Modelo de Dados

### **Tabela: events**
```
┌─────────────────────────────────────┐
│           events                    │
├─────────────────────────────────────┤
│ id (UUID)                  PRIMARY  │
│ type (String)              INDEX    │
│ payload (JSONB)                     │
│ idempotency_key (String)   UNIQUE   │
│ created_at (DateTime)               │
└─────────────────────────────────────┘
```
- **Idempotência**: Mesma `idempotency_key` = mesmo evento
- **Payload flexível**: JSONB para dados estruturados

### **Tabela: notifications**
```
┌──────────────────────────────────────┐
│        notifications                 │
├──────────────────────────────────────┤
│ id (UUID)                   PRIMARY  │
│ event_id (FK → events)      INDEX    │
│ user_id (UUID)              INDEX    │
│ type (String)                        │
│ status (pending|processing) INDEX    │
│ payload (JSONB)                      │
│ locked_at (DateTime)        INDEX    │
│ scheduled_at (DateTime)     INDEX    │
│ processed_at (DateTime)              │
│ retry_count (Integer)                │
│ deduplication_key (String)  INDEX    │
│ version (Integer)                    │
└──────────────────────────────────────┘
```

**Índices Otimizados:**
- `idx_notifications_queue`: Status + scheduled_at + created_at
- `idx_notifications_pending`: Partial index para pending
- `idx_notifications_user_status`: user_id + status + scheduled_at
- `idx_notifications_locked`: Para detectar timeouts

### **Tabela: notification_counters**
```
┌──────────────────────────────────────┐
│    notification_counters             │
├──────────────────────────────────────┤
│ user_id (UUID)              PRIMARY  │
│ unread_count (Integer)               │
└──────────────────────────────────────┘
```
- Contador rápido de notificações não lidas
- Limite por usuário configurável

### **Tabela: failed_notifications**
```
┌──────────────────────────────────────┐
│    failed_notifications              │
├──────────────────────────────────────┤
│ id (UUID)                   PRIMARY  │
│ notification_id (UUID)               │
│ event_id (UUID)                      │
│ user_id (UUID)                       │
│ type (String)                        │
│ payload (JSONB)                      │
│ error_message (String)               │
│ failed_at (DateTime)                 │
│ retry_count (Integer)                │
└──────────────────────────────────────┘
```
- Rastreamento de falhas
- Auditoria de erros

---

## 🔄 Fluxo de Eventos

### **1. Criação de Evento (Request)**
```
POST /events
├─ EventService.create_event()
│  ├─ Insert Event (idempotente)
│  ├─ FanOut: Expande em notificações
│  ├─ NotificationService: Cria batch
│  ├─ CounterService: Incrementa contador
│  └─ Transaction: Tudo ou nada
└─ Response: event_id (UUID)
```

**Garantias:**
- ✅ Idempotência via `idempotency_key`
- ✅ Transação ACID
- ✅ Deduplicação de notificações

### **2. Processamento de Notificação (Worker)**
```
fetch_notifications()
├─ Lock: SELECT ... FOR UPDATE SKIP LOCKED
├─ Queriar pending + retry (timeout detection)
├─ Batch size: 10 notificações
├─ Status: pending → processing (lock)
├─ process_notification() para cada uma
├─ Rate Limiter: 600 por minuto
├─ Retry: MAX 5 tentativas
└─ Handle falhas: Log em failed_notifications
```

**Padrões Implementados:**
- 🔒 Pessimistic Locking com SKIP LOCKED
- ⏱️ Timeout detection (30 segundos)
- 🔄 Retry automático
- 📊 Rate limiting (Token Bucket)
- 📈 Escalável horizontalmente

---

## 📁 Estrutura do Projeto

```
proccessment_events_system/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + routers
│   ├── worker.py                  # Background worker
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy setup
│   │   ├── get_db.py              # DB session dependency
│   │   └── models.py              # SQLAlchemy models
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── events.py              # POST /events
│   │   ├── counter.py             # POST /counter/{user_id}/increment
│   │   └── health.py              # GET /health
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── event_service.py       # Lógica de eventos
│   │   ├── notification_service.py # Lógica de notificações
│   │   ├── counter_service.py     # Lógica de contadores
│   │   └── fanout.py              # Expansão de eventos
│   │
│   └── utils/
│       ├── hash_generate.py       # Hash para deduplicação
│       ├── init_db.py             # Setup inicial do BD
│       ├── rate_limiter.py        # Token bucket limiter
│       └── schemas.py             # Pydantic schemas
│
├── test/
│   ├── client.py                  # HTTP client para testes
│   ├── test_counter_concurrency.py # Testes de concorrência
│   └── test_events.py             # Testes de eventos
│
├── docker-compose.yaml            # Orquestração de containers
├── Dockerfile                      # Build da imagem
├── Makefile                        # Scripts utilitários
├── requirements.txt               # Dependências Python
└── README.md                       # Este arquivo
```

---

## 🔑 Padrões e Boas Práticas

### 1. **Idempotência**
```python
stmt = (
    insert(Event)
    .values(...)
    .on_conflict_do_nothing(index_elements=["idempotency_key"])
)
```
- Mesmo request, mesmo resultado
- Chave de idempotência obrigatória

### 2. **Pessimistic Locking com SKIP LOCKED**
```python
pending_stmt = (
    select(Notification)
    .where(status == "pending")
    .with_for_update(skip_locked=True)  # Pula bloqueados
)
```
- Workers não se bloqueiam um ao outro
- Escalável horizontalmente
- Evita deadlocks

### 3. **Timeout Detection**
```python
timeout_limit = now - timedelta(seconds=30)
retry_stmt = (
    select(Notification)
    .where(locked_at < timeout_limit)  # Detecta travamentos
)
```
- Notificações travadas > 30s voltam para processamento
- Retry automático
- MAX 5 tentativas

### 4. **Deduplicação**
```python
deduplication_key = generate_hash({
    "type": payload["type"],
    "user_id": payload["data"]["user_id"]
})
```
- Evita notificações duplicadas
- Chave baseada em conteúdo

### 5. **Rate Limiting (Token Bucket)**
```python
class RateLimiter:
    def __init__(self, rate_per_minute=600):
        self.rate_per_second = rate_per_minute / 60
```
- Configurável por minuto
- Suave e precisoe
- Sem fila de espera

### 6. **Índices Otimizados**
- Índice composto para fila: `(status, scheduled_at, created_at)`
- Índice partial para pending: `WHERE status = 'pending'`
- Índice por usuário: `(user_id, status, scheduled_at)`

---

## 🛠️ Stack de Tecnologias

| Camada  | Tecnologia | Versão |
|---------|-----------|--------|
| **API** | FastAPI | 0.110.0 |
| **Servidor** | Uvicorn | 0.27.1 |
| **ORM** | SQLAlchemy | 2.0.29 |
| **Banco** | PostgreSQL | 15 |
| **Driver** | psycopg2 | 2.9.9 |
| **Validação** | Pydantic | 2.6.4 |
| **Env** | python-dotenv | 1.0.1 |
| **Python** | Python | 3.11 |

---

## 📦 Setup e Instalação

### Pré-requisitos
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15 (via Docker)

### Opção 1: Docker Compose (Recomendado)

```bash
# Build e start (1 worker)
make build

# Ou com múltiplos workers
make build WORKERS=3

# Stop
make stop
```

### Opção 2: Local

```bash
# 1. Setup Python
python -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` no Windows
pip install -r requirements.txt

# 2. Setup Banco de Dados
docker run -d \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=events_db \
  -p 5432:5432 \
  postgres:15

# 3. Variáveis de Ambiente
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/events_db
EOF

# 4. Inicializar Banco
python -m app.utils.init_db

# 5. Rodar API
uvicorn app.main:app --reload --port 8000

# 6. Em outro terminal: Rodar Worker
python -m app.worker
```

---

## 🚀 Uso

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Criar um Evento
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "type": "user_event",
    "idempotency_key": "key-123",
    "payload": {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "action": "login"
    }
  }'
```

**Resposta:**
```json
{
  "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

### 3. Incrementar Contador
```bash
curl -X POST http://localhost:8000/counter/550e8400-e29b-41d4-a716-446655440000/increment
```

### 4. Verificar Notificações (Database)
```bash
docker exec -it db psql -U postgres -d events_db -c "SELECT * FROM notifications LIMIT 5;"
```

---

## 🧪 Testes

```bash
# Testes de concorrência
python -m pytest test/test_counter_concurrency.py -v

# Testes de eventos
python -m pytest test/test_events.py -v

# Todos os testes
python -m pytest test/ -v
```

---

## 📊 Monitoramento

### Adminer (Admin de BD)
- URL: http://localhost:8081
- Server: `db`
- User: `postgres`
- Password: `postgres`
- Database: `events_db`

### Queries Úteis

**Notificações Pendentes:**
```sql
SELECT id, user_id, type, status, created_at 
FROM notifications 
WHERE status = 'pending' 
ORDER BY created_at DESC 
LIMIT 10;
```

**Notificações Travadas:**
```sql
SELECT id, user_id, locked_at, 
  EXTRACT(EPOCH FROM (NOW() - locked_at)) as locked_seconds
FROM notifications 
WHERE status = 'processing' 
AND locked_at IS NOT NULL;
```

**Contadores por Usuário:**
```sql
SELECT * FROM notification_counters WHERE unread_count > 0;
```

**Falhas Recentes:**
```sql
SELECT * FROM failed_notifications 
ORDER BY failed_at DESC LIMIT 20;
```

---

## ⚙️ Configurações Importantes

**app/worker.py:**
```python
BATCH_SIZE = 10              # Notificações por batch
TIMEOUT_SECONDS = 30         # Timeout de lock
rate_limiter = RateLimiter(rate_per_minute=600)  # 10/segundo
MAX_RETRIES = 5              # Tentativas máximas
```

**app/services/event_service.py:**
```python
USER_NOTIFICATION_LIMIT = 50  # Notificações máx por usuário
```

---

## 🔒 Segurança e Confiabilidade

- ✅ **Transações ACID**: Correção de dados garantida
- ✅ **Idempotência**: Duplicatas automáticas evitadas
- ✅ **Travamento Pessimista**: Race conditions prevenidas
- ✅ **Retry Automático**: Falhas temporárias recuperadas
- ✅ **Timeout Detection**: Workers mortos detectados
- ✅ **Rate Limiting**: Não sobrecarga o sistema
- ✅ **Índices Otimizados**: Performance garantida

---

## 📈 Escalabilidade

### Horizontal Scaling
```bash
# 3 workers
make build WORKERS=3

# 5 workers
make build WORKERS=5
```

**Características:**
- Workers independentes compartilham fila (BD)
- SKIP LOCKED previne contention
- Escalável até ~100+ workers

### Performance Esperada
- **Events/segundo**: 1000+
- **Latência p95**: < 100ms
- **Throughput notificações**: 600/min com 1 worker

---

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| Porta 5432 em uso | `docker kill <container>` ou trocar porta |
| Conexão DB recusada | Aguardar healthcheck: `docker compose logs db` |
| Worker não processa | Verificar status: `SELECT COUNT(*) FROM notifications WHERE status = 'pending'` |
| Rate limiting muito agressivo | Aumentar `rate_per_minute` em `app/worker.py` |
| Muitas falhas | Verificar `failed_notifications` table |

---

## 📚 Recursos e Referências

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)
- [PostgreSQL Docs](https://www.postgresql.org/docs)
- [Pessimistic Locking Pattern](https://en.wikipedia.org/wiki/Lock_(database))
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)

---

## 📄 Licença

Este projeto é de estudo e pode ser usado livremente.

---

## 👤 Autor

Desenvolvido como projeto de aprendizado em arquiteturas backend modernas.
│   ├── test/
│   ├── worker.py
│   ├── routes/
│   ├── services/
│   └── utils/
├── docker-compose.yaml
├── Dockerfile
└── requirements.txt
```

---

## ⚙️ Key Concepts Implemented

### 1. Database as Queue

Notifications are stored in a table and consumed using:

* `FOR UPDATE SKIP LOCKED`
* `status` field (`pending`, `processing`, `done`)
* `locked_at` for task leasing

---

### 2. Concurrency Control

Multiple workers can run safely using:

* Pessimistic locking
* Timeout-based reprocessing

---

### 3. Task Leasing

If a worker crashes, tasks are recovered using:

```
locked_at < now - timeout
```

---

### 4. Rate Limiting

Worker throughput is controlled using a **token bucket algorithm**, ensuring:

* Controlled processing rate
* Backpressure handling

---

## ⚠️ Disclaimer

This is a **learning project**, but it is intentionally built using patterns found in production systems.

---

## 🎯 Learning Goals

This project focuses on:

* Distributed systems fundamentals
* Database-driven queues
* Concurrency and locking
* Throughput vs latency trade-offs
* Fault tolerance patterns

---
