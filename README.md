# 📦 Processment Events System

## 🚀 Overview

This project is a **study-oriented event processing system** designed to simulate real-world backend challenges such as:

* Event-driven architecture
* Queue persistence using a relational database
* Concurrent workers with locking
* Rate limiting
* Retry strategies (planned)

The goal is not just functionality, but to build the system using **production-grade patterns and practices**.

---

## 🧠 Architecture

The system follows a simplified event-driven pipeline:

```
Client → API → Event → Notification Queue (DB) → Worker → Processing
```

### Components

* **API (FastAPI)**

  * Receives events
  * Persists them in the database
  * Generates notifications

* **Database (PostgreSQL)**

  * Stores events and acts as a persistent queue

* **Worker**

  * Fetches pending notifications
  * Applies locking (pessimistic locking with SKIP LOCKED)
  * Processes them respecting rate limits

---

## 📂 Project Structure

```
.
├── app
│   ├── database/
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

## 🔌 API

### Create Event

**POST** `/events`

#### Request

```json
{
  "type": "user.created",
  "payload": {
    "user_id": "123",
    "email": "user@email.com"
  }
}
```

#### Response

```json
{
  "event_id": "<uuid>"
}
```

---

## 🧪 Running the Project

### Build with one worker

```bash
make build 
```

### Build more workers

```bash
make build WORKERS=<value>
```


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
