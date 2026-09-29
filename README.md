# ⚡ OnCall Memory — Self-Learning Incident Response Agent

> **An on-call incident response agent that remembers past production incidents and gets smarter with every one.**  
> Built for the Hackathon judged on **Innovation (30%)**, **Use of Hindsight Memory (25%)**, **Technical Implementation (20%)**, **UX (15%)**, and **Real-world Impact (10%)**.

---

## 🚨 The Problem

In high-velocity production environments (such as our fictional fintech **Northwind Pay**), on-call engineers face two critical pain points during SEV-1 outages:

1. **Organizational Amnesia**: Teams solve the exact same Postgres connection leak or Kafka consumer lag multiple times. The solution lives inside Slack threads or forgotten Notion post-mortems, causing high Mean Time to Resolution (MTTR).
2. **Dangerous Generic Advice**: Plain LLMs offer textbook answers ("reboot the database", "increase timeouts"). In production, rebooting a primary database under heavy load triggers catastrophic **thundering-herd crash loops** (INC-2024-0301).

**OnCall Memory** solves this by establishing a persistent, bidirectional **Hindsight Memory Bank**. It recalls what actually fixed past incidents, warns engineers against historically failed remediations, and continuously learns from live on-call feedback.

---

## 🏛️ Architecture

```
                          +-------------------------------------------------+
                          |             Browser Dashboard UI                |
                          |  - Side-by-side Before/After Diagnosis          |
                          |  - 3-Step Guided Hackathon Demo Mode            |
                          |  - Live Hindsight Memory Counter & Explorer     |
                          |  - Continuous Feedback Loop Form                |
                          +-----------------------+-------------------------+
                                                  |
                                            HTTP / JSON
                                                  |
                                                  v
                          +-------------------------------------------------+
                          |               FastAPI Server                    |
                          |                 (main.py)                       |
                          +-------+-------------------------------+---------+
                                  |                               |
                   +--------------v---------------+ +-------------v-------------+
                   |     Incident Engine          | |    Systemic Insights      |
                   | (backend/incident_engine.py) | |    (Hindsight Reflect)    |
                   +--------------+---------------+ +-------------+-------------+
                                  |                               |
             +--------------------+-------------------+           |
             |                                        |           |
             v                                        v           |
+--------------------------+             +------------------------v----+
|     Plain LLM Path       |             |   Hindsight Memory Manager  |
|      (No Memory)         |             | (backend/memory_client.py)  |
| - Generic textbook advice|             +--------------+--------------+
| - Low confidence         |                            |
| - Zero company context   |             +--------------+--------------+
+--------------------------+             |  Hindsight Memory SDK (API)  |
                                         |   - retain()   [Ingest]     |
                                         |   - recall()   [Multi-strat]|
                                         |   - reflect()  [Synthesis]  |
                                         +--------------+--------------+
                                                        |
                                         +--------------v--------------+
                                         |    Groq LLM Orchestrator    |
                                         |  - Primary: openai/gpt-oss  |
                                         |  - Fallback: qwen/qwen3-32b |
                                         |  - Grounded with Recalled   |
                                         |    Citations & Fix Traps    |
                                         +-----------------------------+
```

---

## 🧠 How Hindsight Memory is Used

This application directly integrates the official Hindsight API via `hindsight-client`:

### 1. `retain` & `retain_batch` (Continuous Memory Ingestion)
- **Seed Phase (`seed.py`)**: Ingests **25 realistic Northwind Pay incidents** spanning database connection exhaustion, Redis memory evictions, expired TLS certificates, Kafka poison pills, and AWS IAM credential expiration.
- **Feedback Loop**: When an on-call engineer marks a resolution as *"Fix Worked"* or *"Fix Failed"*, `client.retain()` stores the live event, resolution steps, and engineer notes into the `northwind-oncall` bank so future responders immediately benefit from the learning.

```python
# Retaining a live incident resolution into Hindsight
client.retain(
    bank_id="northwind-oncall",
    content=formatted_incident_story,
    context="service:checkout-service",
    metadata={
        "incident_id": "INC-2024-0929",
        "service": "checkout-service",
        "who_fixed_it": "Sarah Chen",
        "fix_status": "SUCCESS"
    },
    retain_async=False
)
```

### 2. `recall` (Multi-Strategy Retrieval)
- When a new alert and raw stack traces arrive, `client.recall(bank_id="northwind-oncall", query=alert_and_logs, budget="high")` executes multi-strategy retrieval (semantic similarity, keyword BM25, graph traversal, and temporal proximity).
- Returns structured memory units containing:
  - Exact historical root causes
  - Who solved it and how long it took (MTTR)
  - Historical **FAILED attempts** (e.g. *"Do not hard-reboot RDS: caused 85 min thundering-herd downtime in INC-2024-0301"*)
  - Exact shell commands, SQL queries, or configuration parameters used previously

### 3. `reflect` (Systemic Architecture Insights)
- Clicking the **"Systemic Insights"** button calls `client.reflect()`.
- Hindsight runs an autonomous agentic reasoning loop across the entire memory bank to answer:
  > *"What patterns keep causing our incidents and what should we fix permanently?"*
- Synthesizes recurring failure modes (e.g., coroutine connection leaks, unpartitioned Kafka consumers) into long-term infrastructure hardening proposals.

```python
answer = client.reflect(
    bank_id="northwind-oncall",
    query="What patterns keep causing our incidents and what should we fix permanently?",
    budget="high"
)
print(answer.text)
```

---

## 🚀 Quick Start & Setup

### Prerequisites
- Python 3.10+
- (Optional) Groq API Key and Hindsight credentials. If keys are not provided, the application runs seamlessly in local resilient simulation mode.

### 1. Clone & Enter Project
```bash
cd C:\Users\sri54\.gemini\antigravity\scratch\oncall-memory
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your API keys:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_BANK_ID=northwind-oncall
```

### 4. Seed the Memory Bank
Populate the Hindsight bank with 25 realistic production incidents:
```bash
python seed.py
```

### 5. Launch the Server
Start the FastAPI server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

## 🎯 Hackathon Demo Script (3-Step Walkthrough)

Click the **"Demo Mode"** button in the top navigation bar to launch the interactive judge scenario:

### 1. Step 1: Initial Alert (Postgres Connection Pool Exhaustion)
- Click **"Load & Run Step"**.
- **Without Memory (Left)**: Suggests generic actions: *"Inspect database metrics, restart application pods, consider scaling up"*. Confidence is ~58%.
- **With Hindsight Memory (Right)**: Pinpoints that an unclosed connection handle in the cart audit coroutine caused max_connections=200 exhaustion (matches INC-2024-0102). Recommends the exact `SELECT pg_terminate_backend(pid)...` query used by Marcus Vance. Confidence: **96%**.

### 2. Step 2: Cross-Symptom Recall (Cart 504 Gateway Timeout)
- Advance to **Step 2**. The alert presents under completely different symptoms: *"HTTP 504 Gateway Timeout on Cart API"*.
- **Without Memory**: Diagnoses an API gateway or ingress network timeout.
- **With Hindsight Memory**: Connects the 504 gateway timeout to database connection contention (INC-2024-0418) rather than network issues, demonstrating Hindsight's multi-hop semantic association!

### 3. Step 3: Learning from Past Failures
- Advance to **Step 3**. An engineer asks: *"Should we just do a hard reboot on the RDS primary?"*
- **With Hindsight Memory**: Detects that in INC-2024-0301, Devon Reed tried a hard reboot which triggered WAL recovery and an immediate 500-pod thundering herd that crashed the database for 85 minutes. The agent **explicitly warns against restarting the database**, recommending PgBouncer connection throttling instead.

---

## 📸 Screenshots & UI Preview

```
+-----------------------------------------------------------------------------------------------+
|  ⚡ OnCall Memory | Northwind Pay       [Bank: northwind-oncall | 25 Memories] [💡 Insights]  |
+-----------------------------------------------------------------------------------------------+
|  1-Click Scenarios: [ Postgres Pool Exhaustion ] [ Stripe 429 ] [ Kafka Lag ]                |
|  Alert: P1 ALERT: Checkout Service HTTP 500 Spike & Connection Pool Starvation                |
|  [ ⚡ Run Side-by-Side Analysis ]                                                             |
+---------------------------------------------------------------+-------------------------------+
|                 WITHOUT MEMORY (Generic LLM)                  |     WITH HINDSIGHT MEMORY     |
|                   Zero Historical Context                     |  Recalled from 3 past events  |
|                                                               |                               |
| Root Cause: Generic resource exhaustion or backend load       | Root Cause: Leaked coroutine  |
| Confidence: 58% [========                  ]                  | Confidence: 96% [===========] |
| Steps:                                                        | Steps:                        |
|  - Check system metrics                                       |  - Run pg_terminate_backend() |
|  - Restart application pods                                   |  - Scale pods 12 -> 4         |
|  - Increase max_connections                                   |  - Patch pgbouncer session    |
|                                                               |                               |
|                                                               | ⚠️ Trap: Do NOT reboot RDS!   |
|                                                               | (Caused 85m thundering herd)  |
|                                                               | Citations:                    |
|                                                               | [INC-2024-0102] Marcus Vance  |
|                                                               | [INC-2024-0301] Failed Reboot |
+---------------------------------------------------------------+-------------------------------+
|  🔄 On-Call Feedback Loop: [✅ Fix Worked] [❌ Fix Failed]                                    |
|  Notes: Terminated idle connections and deployed pgbouncer patch.                             |
|  [ 💾 Retain Resolution in Hindsight Bank ] -> Toast: "Memory updated: Retained INC-2024..."  |
+-----------------------------------------------------------------------------------------------+
```

---

## 🧪 Testing

Run the automated test suite verifying all 7 endpoints, side-by-side generation, feedback retention, and reflection:
```bash
python test_app.py
```

Output:
```
ALL 7 END-TO-END TESTS PASSED SUCCESSFULLY!
```

---

## 🏆 Hackathon Criteria Alignment

| Criteria | Weight | Implementation in OnCall Memory |
|:---|:---:|:---|
| **Innovation** | 30% | First on-call agent that prevents catastrophic SRE mistakes by remembering **failed remediations** (anti-patterns) alongside successful fixes. |
| **Use of Hindsight** | 25% | Comprehensive use of `retain`, `retain_batch`, `recall` (with citations & raw fact inspection), and `reflect` (systemic architecture debt synthesis). |
| **Technical Implementation** | 20% | Clean Python + FastAPI backend, typed Hindsight client, Groq dual-model LLM fallback (`openai/gpt-oss-120b` & `qwen/qwen3-32b`), resilient offline fallback. |
| **UX** | 15% | High-contrast dark ops dashboard, live memory counter, prominent side-by-side before/after view, and interactive 3-step demo wizard for judges. |
| **Real-world Impact** | 10% | Directly reduces SEV-1 MTTR from hours to minutes and eliminates recurring outages in mission-critical payment infrastructure. |

---

*Built with ❤️ for the Hindsight Hackathon.*
