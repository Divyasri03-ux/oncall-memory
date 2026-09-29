"""
Sample incidents and seed data for Northwind Pay OnCall Memory.
Contains 25 realistic production incidents with stack traces, root causes,
remediation steps, resolution times, engineers, and outcomes (success/failed).
"""

SEED_INCIDENTS = [
    {
        "id": "INC-2024-0102",
        "date": "2024-01-02 14:22 UTC",
        "service": "checkout-service",
        "title": "Postgres Connection Pool Exhaustion in Checkout",
        "error_logs": """[checkout-service] 2024-01-02 14:21:04 ERROR django.db.utils.OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections
[checkout-service] 2024-01-02 14:21:05 CRITICAL pool_manager.py:88 - ConnectionPoolExhausted: Pool max_connections=200 reached. Active: 200, Waiting: 142.
Traceback (most recent call last):
  File "apps/checkout/views.py", line 112, in process_cart
    with db.transaction.atomic():
  File "django/db/backends/base/base.py", line 219, in get_new_connection
    return Database.connect(**conn_params)
OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections""",
        "root_cause": "A new release omitted a database connection close inside the asynchronous cart audit webhook thread, causing orphaned database connections to accumulate until max_connections was hit.",
        "fix_steps": "1. Run SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - INTERVAL '5 minutes';\n2. Scaled down checkout-worker pods from 12 to 4 to relieve immediate pool pressure.\n3. Deployed hotfix v2.14.1 adding explicit db.connections.close_all() in cart audit thread.",
        "time_to_resolve": "38 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["postgres", "connection-pool", "leak", "checkout-service"]
    },
    {
        "id": "INC-2024-0115",
        "date": "2024-01-15 09:10 UTC",
        "service": "payment-gateway",
        "title": "Adyen & Stripe API Rate Limiting (HTTP 429) on Card Processing",
        "error_logs": """[payment-gateway] 2024-01-15 09:08:44 WARN providers/stripe_client.py:145 - 429 Client Error: Too Many Requests for url: https://api.stripe.com/v1/payment_intents
[payment-gateway] 2024-01-15 09:08:45 ERROR gateway/orchestrator.py:210 - UpstreamPaymentProviderRateLimit: Rate limit quota exceeded (100 req/sec limit).
[payment-gateway] 2024-01-15 09:08:45 ERROR gateway/views.py:76 - 503 Service Unavailable returned to client token=tok_991823""",
        "root_cause": "Black Friday marketing flash-sale triggered burst traffic of 280 payments/sec against our Stripe tier limit of 100/sec, because dynamic circuit breaking and client-side token bucket rate limiting were disabled during morning deploy.",
        "fix_steps": "1. Enabled Redis-backed LeakyBucket token limiter with dynamic backoff in payment-gateway config.\n2. Switched 40% of non-US card transactions to secondary Adyen fallback rail.\n3. Requested emergency TPS increase from Stripe account executive.",
        "time_to_resolve": "24 minutes",
        "who_fixed_it": "Elena Rostova (Payments Lead)",
        "fix_status": "SUCCESS",
        "tags": ["rate-limit", "stripe", "adyen", "circuit-breaker", "payment-gateway"]
    },
    {
        "id": "INC-2024-0128",
        "date": "2024-01-28 18:45 UTC",
        "service": "settlement-pipeline",
        "title": "Kafka Consumer Lag Surge due to Poison Pill JSON Payload",
        "error_logs": """[settlement-pipeline] 2024-01-28 18:43:11 ERROR kafka_consumer.py:102 - RecordProcessingException in partition 3 offset 9028114
Traceback (most recent call last):
  File "workers/settlement.py", line 45, in handle_message
    amount_cents = int(record['payload']['transaction_amount'])
ValueError: invalid literal for int() with base 10: 'null'
[settlement-pipeline] 2024-01-28 18:44:00 CRITICAL monitoring/lag.py:19 - Consumer group 'settlement-workers' lag exceeded 85,000 records!""",
        "root_cause": "A mobile client bug sent string 'null' instead of numeric amount in payload. Consumer lacked Dead Letter Queue (DLQ) exception trapping and kept retrying the same offset endlessly, halting the entire partition.",
        "fix_steps": "1. Manually committed offset past 9028114 on partition 3 using kafka-consumer-groups.sh.\n2. Deployed hotfix wrapping JSON deserialization in try/except and pushing malformed records to settlement-dlq topic.\n3. Scaled consumer replicas to 8 to burn down accumulated lag in 15 mins.",
        "time_to_resolve": "32 minutes",
        "who_fixed_it": "Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["kafka", "consumer-lag", "poison-pill", "dlq", "settlement-pipeline"]
    },
    {
        "id": "INC-2024-0205",
        "date": "2024-02-05 03:15 UTC",
        "service": "auth-api",
        "title": "Expired TLS Wildcard Certificate on *.internal.northwind.pay",
        "error_logs": """[auth-api] 2024-02-05 03:14:02 ERROR ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate has expired (_ssl.c:1007)
[auth-api] 2024-02-05 03:14:03 CRITICAL vault/client.py:54 - Unable to connect to Vault cluster https://vault.internal.northwind.pay:8200
requests.exceptions.SSLError: HTTPSConnectionPool(host='vault.internal.northwind.pay', port=8200): Max retries exceeded with url: /v1/auth/jwt/login""",
        "root_cause": "Cert-manager automated Let's Encrypt / Vault ACME renewal cron was blocked because security group rule 443 egress to the internal ACME boulder CA was removed during Terraform VPC refactoring.",
        "fix_steps": "1. Manually issued and applied new wildcard cert via step-ca CLI directly to Kubernetes secret internal-wildcard-tls.\n2. Rolled ingress-nginx deployment.\n3. Restored port 443 egress in security_groups.tf and verified cert-manager certificate status.",
        "time_to_resolve": "27 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["tls", "certificate", "cert-manager", "vault", "auth-api"]
    },
    {
        "id": "INC-2024-0219",
        "date": "2024-02-19 11:30 UTC",
        "service": "fraud-detector",
        "title": "Redis Cluster OOM & Eviction Cascade Causing False Positives",
        "error_logs": """[fraud-detector] 2024-02-19 11:28:12 ERROR redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'.
[fraud-detector] 2024-02-19 11:28:15 WARN cache.py:91 - Redis cluster node 10.0.3.41 hit 99.8% memory utilization (16GB/16GB). Eviction policy 'noeviction' rejected SETNX.
[fraud-detector] 2024-02-19 11:29:01 CRITICAL rules_engine.py:302 - Cannot fetch IP velocity window. Falling back to FAIL_CLOSED, blocking 1,200 valid transactions!""",
        "root_cause": "Fraud rule update introduced 30-day sliding IP velocity counters without setting a TTL on the Redis hash keys. Millions of ephemeral keys overwhelmed Redis memory within 48 hours.",
        "fix_steps": "1. Temporarily changed maxmemory-policy to volatile-lru using CONFIG SET maxmemory-policy allkeys-lru.\n2. Ran background scan script to expire all keys matching 'fraud:ip:*' older than 24 hours.\n3. Shipped code fix guaranteeing EXPIRE 86400 on all newly created velocity keys.",
        "time_to_resolve": "45 minutes",
        "who_fixed_it": "Elena Rostova (Payments Lead)",
        "fix_status": "SUCCESS",
        "tags": ["redis", "oom", "eviction", "ttl", "fraud-detector"]
    },
    {
        "id": "INC-2024-0301",
        "date": "2024-03-01 16:10 UTC",
        "service": "checkout-service",
        "title": "FAILED REMEDIATION: Uncontrolled DB Restart under Heavy Traffic",
        "error_logs": """[checkout-service] 2024-03-01 16:08:20 ERROR psql: server closed the connection unexpectedly
[checkout-service] 2024-03-01 16:09:10 CRITICAL k8s/pod_controller: Container checkout-app CrashLoopBackOff.
PostgreSQL: FATAL: the database system is in recovery mode.
PostgreSQL: LOG: redo starts at 1F/34A0108...
PostgreSQL: FATAL: sorry, too many clients already (max_connections=200 exhausted in 1.4s post restart)""",
        "root_cause": "Engineer attempted to quickly clear stuck database queries by restarting the Primary AWS RDS PostgreSQL instance directly. This triggered write-ahead log recovery and when DB came up, 500 app pods slammed the database simultaneously, knocking it down repeatedly.",
        "fix_steps": "FAILED ATTEMPT: Hard DB reboot without queuing traffic first.\nACTUAL FIX: Scaled Kubernetes deployments to 0 replicas, let DB complete crash recovery cleanly, enabled PgBouncer connection pooling with max_client_conn=2000 and default_pool_size=40, then scaled apps back gradually.",
        "time_to_resolve": "85 minutes",
        "who_fixed_it": "Devon Reed (Junior DevOps) & Marcus Vance (Staff Infra)",
        "fix_status": "FAILED",
        "failed_reason": "Hard-restarting database while all client pods are running caused an instant connection stampede (thundering herd) and repeated DB crash loops.",
        "tags": ["postgres", "thundering-herd", "failed-fix", "pgbouncer", "checkout-service"]
    },
    {
        "id": "INC-2024-0312",
        "date": "2024-03-12 21:05 UTC",
        "service": "notification-worker",
        "title": "OOMKilled Pods in Notification Delivery due to Unbounded In-Memory Batching",
        "error_logs": """[k8s-events] 2024-03-12 21:04:12 Reason: OOMKilled, ExitCode: 137
[notification-worker] 2024-03-12 21:04:00 WARN memory_tracker: RSS memory: 1980MB / limit 2048MB
[notification-worker] 2024-03-12 21:04:08 CRITICAL SystemExit: Process killed by kernel cgroup out-of-memory killer.""",
        "root_cause": "Notification push service attempted to buffer SMS and email webhook events in an in-memory Python list during a SendGrid outage, ballooning memory usage past container limit of 2GB.",
        "fix_steps": "1. Raised container memory limit to 4GB temporarily to unblock queue processing.\n2. Rewrote batch buffer to spill to local disk FIFO queue when queue depth > 1,000.\n3. Added backpressure circuit breaker to stop reading from RabbitMQ when memory > 80%.",
        "time_to_resolve": "19 minutes",
        "who_fixed_it": "Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["oomkilled", "kubernetes", "memory-leak", "backpressure", "notification-worker"]
    },
    {
        "id": "INC-2024-0324",
        "date": "2024-03-24 08:40 UTC",
        "service": "ledger-db",
        "title": "Postgres Table Lock Deadlock during Schema Migration",
        "error_logs": """[ledger-db] 2024-03-24 08:38:52 ERROR postgres: Process 41203 waits for AccessExclusiveLock on table "transactions"; blocked by process 41189.
[ledger-db] 2024-03-24 08:38:55 ERROR postgres: Process 41189 waits for ShareLock on transaction 984021; blocked by process 41203.
[ledger-db] 2024-03-24 08:39:00 FATAL: deadlock detected. Detail: See pg_locks for active graph.""",
        "root_cause": "Migration ran ALTER TABLE transactions ADD COLUMN audit_hash VARCHAR(64) DEFAULT NULL without lock_timeout. A slow analytical reporting query held ShareLock, causing the migration to queue and lock all subsequent INSERTs.",
        "fix_steps": "1. Canceled migration process: SELECT pg_cancel_backend(41203);\n2. Added SET lock_timeout = '2s'; and ran migration with zero-downtime pattern (ADD COLUMN without table lock, followed by backfill).\n3. Killed remaining zombie analytical queries.",
        "time_to_resolve": "14 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["postgres", "deadlock", "lock-timeout", "migration", "ledger-db"]
    },
    {
        "id": "INC-2024-0404",
        "date": "2024-04-04 13:20 UTC",
        "service": "api-gateway",
        "title": "CoreDNS CPU Saturation Causing DNS Resolution Timeouts in K8s",
        "error_logs": """[api-gateway] 2024-04-04 13:18:10 ERROR urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='auth.internal.northwind.pay'): Name or service not known
[api-gateway] 2024-04-04 13:18:12 ERROR httpx.ConnectError: [Errno -3] Temporary failure in name resolution
[kube-system] 2024-04-04 13:19:00 WARN coredns pod coredns-7c5b9b665-m2z4p CPU throttling at 98%.""",
        "root_cause": "Services with default ndots:5 in resolv.conf were making 5 recursive search attempts for every external HTTPS call, creating 45,000 QPS on CoreDNS pods.",
        "fix_steps": "1. Scaled CoreDNS deployment from 2 to 10 replicas immediately.\n2. Enabled NodeLocal DNSCache DaemonSet across all EKS nodes.\n3. Configured ndots:2 in base service deployment templates.",
        "time_to_resolve": "22 minutes",
        "who_fixed_it": "Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["dns", "coredns", "kubernetes", "timeout", "api-gateway"]
    },
    {
        "id": "INC-2024-0418",
        "date": "2024-04-18 17:50 UTC",
        "service": "checkout-service",
        "title": "Cart Latency Spike and HTTP 504 Gateway Timeouts under Database Connection Contention",
        "error_logs": """[api-gateway] 2024-04-18 17:48:30 ERROR upstream_connect_timeout: upstream 10.0.4.18:8000 timed out (504 Gateway Timeout)
[checkout-service] 2024-04-18 17:48:32 WARN db_pool: pool acquire wait time exceeded 30,000ms. Available connections: 0 / 180.
[checkout-service] 2024-04-18 17:49:01 ERROR views.py:221 - User checkout checkout_token=ch_812739 failed after 30s timeout.""",
        "root_cause": "Unindexed foreign key query on order_items table locked rows during batch inventory sync, causing checkout threads to block waiting for database pool slots, manifesting as 504 timeouts at the API gateway.",
        "fix_steps": "1. Identified blocking query via pg_stat_activity: SELECT * FROM order_items WHERE batch_id = $1 FOR UPDATE;\n2. Terminated blocking backend PID.\n3. Created index concurrently: CREATE INDEX CONCURRENTLY idx_order_items_batch ON order_items(batch_id);\n4. Connection pool wait time immediately dropped from 30,000ms to 4ms.",
        "time_to_resolve": "26 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["postgres", "connection-pool", "504-timeout", "indexing", "checkout-service"]
    },
    {
        "id": "INC-2024-0429",
        "date": "2024-04-29 10:15 UTC",
        "service": "ledger-db",
        "title": "PostgreSQL WAL Disk Full (100% Storage) Halting Database Writes",
        "error_logs": """[ledger-db] 2024-04-29 10:13:40 PANIC: could not write to log file 00000001000003A4000000C1: No space left on device
[ledger-db] 2024-04-29 10:14:00 FATAL: database system was interrupted while in recovery
[apps] 2024-04-29 10:14:05 ERROR psycopg2.OperationalError: could not connect to server: Connection refused""",
        "root_cause": "An abandoned replication slot created for a decommissioned Debezium CDC pipeline prevented PostgreSQL from recycling WAL logs, filling the 500GB volume to 100%.",
        "fix_steps": "1. Dropped inactive replication slot: SELECT pg_drop_replication_slot('debezium_cdc_old');\n2. Triggered manual checkpoint: CHECKPOINT; which reclaimed 380GB of WAL files.\n3. Increased EBS volume storage by 200GB with autoscaling enabled.",
        "time_to_resolve": "35 minutes",
        "who_fixed_it": "Devon Reed (Junior DevOps) & Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["postgres", "wal", "disk-full", "replication-slot", "ledger-db"]
    },
    {
        "id": "INC-2024-0511",
        "date": "2024-05-11 15:40 UTC",
        "service": "settlement-pipeline",
        "title": "FAILED REMEDIATION: Blindly Increasing Consumer Group Threads Caused Lock Storm",
        "error_logs": """[settlement-pipeline] 2024-05-11 15:38:22 ERROR settlement_worker: ThreadPoolExecutor saturated (500 threads).
[settlement-pipeline] 2024-05-11 15:39:10 CRITICAL postgres: deadlocks detected on table settlement_batches. 48 concurrent transactions waiting for row lock.""",
        "root_cause": "On-call engineer observed Kafka lag and dialed worker concurrency from 20 to 100 per pod. Rather than speeding up processing, the 100 threads competed for the same settlement batch locks in PostgreSQL, creating massive deadlocks and zero throughput.",
        "fix_steps": "FAILED ATTEMPT: Increased consumer thread pool to 100.\nACTUAL FIX: Reverted concurrency to 15 per pod, introduced Kafka partition key partitioning by merchant_id so each merchant batch was handled by a single dedicated thread with zero lock contention.",
        "time_to_resolve": "62 minutes",
        "who_fixed_it": "Devon Reed (Junior DevOps) & Elena Rostova (Payments Lead)",
        "fix_status": "FAILED",
        "failed_reason": "Increasing thread count without partitioning keys created severe row lock contention in the database instead of clearing queue lag.",
        "tags": ["kafka", "deadlock", "failed-fix", "concurrency", "settlement-pipeline"]
    },
    {
        "id": "INC-2024-0523",
        "date": "2024-05-23 20:05 UTC",
        "service": "payment-gateway",
        "title": "Circuit Breaker Stuck Open on Adyen Webhook Processing",
        "error_logs": """[payment-gateway] 2024-05-23 20:03:15 WARN circuit_breaker.py:89 - CircuitBreaker 'adyen-notification' is OPEN. Fast-failing requests.
[payment-gateway] 2024-05-23 20:04:00 ERROR webhooks/adyen.py:51 - CircuitBreakerOpenException: Service rejecting inbound notification events.
[monitoring] 2024-05-23 20:04:30 ALERT Adyen webhook success rate dropped to 0% for 5 minutes.""",
        "root_cause": "A 10-second transient network blip caused 5 consecutive timeouts, tripping PyBreaker to OPEN. The reset timeout was misconfigured in seconds rather than milliseconds (reset_timeout=3600 instead of 30), keeping the breaker open for 1 hour.",
        "fix_steps": "1. Reset circuit breaker state in Redis via redis-cli DEL cb:adyen-notification:state.\n2. Patched config setting reset_timeout=30 and half_open_max_trials=5.\n3. Triggered webhook replay from Adyen customer portal for missed 280 transactions.",
        "time_to_resolve": "16 minutes",
        "who_fixed_it": "Elena Rostova (Payments Lead)",
        "fix_status": "SUCCESS",
        "tags": ["circuit-breaker", "adyen", "webhooks", "payment-gateway"]
    },
    {
        "id": "INC-2024-0604",
        "date": "2024-06-04 07:25 UTC",
        "service": "auth-api",
        "title": "AWS IAM Role STS Token Expiration Breaking KMS Token Decryption",
        "error_logs": """[auth-api] 2024-06-04 07:23:18 ERROR botocore.exceptions.ClientError: An error occurred (ExpiredToken) when calling the Decrypt operation: The security token included in the request is expired
[auth-api] 2024-06-04 07:23:20 CRITICAL token_service.py:114 - Unable to decrypt customer card token with AWS KMS.
[auth-api] 2024-06-04 07:23:45 ERROR views.py:90 - 500 Internal Server Error returned on /v2/tokens/decrypt""",
        "root_cause": "Kiam/IRSA pod mutating webhook stopped refreshing service account credentials because the OIDC provider thumbprint on the AWS IAM role was altered by an automated CI/CD pipeline.",
        "fix_steps": "1. Restored valid OIDC certificate thumbprint in AWS IAM OpenID Connect provider configuration.\n2. Restarted auth-api pods to force acquisition of fresh STS tokens.\n3. Added alert for STS credential renewal failures > 5 mins before expiry.",
        "time_to_resolve": "21 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["aws", "iam", "sts", "kms", "auth-api"]
    },
    {
        "id": "INC-2024-0619",
        "date": "2024-06-19 14:50 UTC",
        "service": "fraud-detector",
        "title": "RabbitMQ Queue Memory Alarm Blocked All Inbound Event Publishing",
        "error_logs": """[fraud-detector] 2024-06-19 14:48:02 ERROR pika.exceptions.ChannelClosedByBroker: (504, 'CHANNEL_ERROR - queue memory high watermark exceeded')
[fraud-detector] 2024-06-19 14:48:15 CRITICAL amqp_publisher.py:65 - Publisher was blocked by RabbitMQ broker 10.0.2.14:5672
[fraud-detector] 2024-06-19 14:49:00 ERROR producer.py:140 - Inbound fraud evaluation dropped 3,400 messages.""",
        "root_cause": "Dead letter exchange was routing unroutable messages back into the main queue in a tight loop, filling the 8GB RAM watermark on RabbitMQ nodes.",
        "fix_steps": "1. Temporarily raised vm_memory_high_watermark from 0.4 to 0.7 using rabbitmqctl set_vm_memory_high_watermark 0.7.\n2. Purged circular dead letter bindings using rabbitmqadmin delete binding.\n3. Consumers drained backlogged messages within 8 minutes.",
        "time_to_resolve": "28 minutes",
        "who_fixed_it": "Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["rabbitmq", "memory-alarm", "amqp", "dead-letter", "fraud-detector"]
    },
    {
        "id": "INC-2024-0702",
        "date": "2024-07-02 12:10 UTC",
        "service": "checkout-service",
        "title": "Postgres Connection Leak in Celery Background Transaction Verification",
        "error_logs": """[checkout-service] 2024-07-02 12:08:44 ERROR sqlalchemy.pool.impl.QueuePool: Timeout waiting for connection from pool of size 20, max_overflow 10.
[checkout-service] 2024-07-02 12:09:12 CRITICAL tasks.py:77 - OperationalError: connection pool exhausted. Active workers: 30, idle in transaction: 28.
Traceback (most recent call last):
  File "apps/orders/tasks.py", line 42, in verify_order_status
    conn = engine.connect()
TimeoutError: QueuePool limit of size 20 overflow 10 reached, connection timed out, timeout 30.00""",
        "root_cause": "Celery worker task used `engine.connect()` without `with` context manager or `conn.close()`, leaving sessions in `idle in transaction` state after API timeouts.",
        "fix_steps": "1. Executed query to terminate idle transaction leaks: SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND state_change < now() - INTERVAL '2 minutes';\n2. Updated Celery task code with context manager `with engine.begin() as conn:`.\n3. Set `pool_pre_ping=True` and `pool_recycle=1800` in SQLAlchemy engine config.",
        "time_to_resolve": "25 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["postgres", "connection-pool", "celery", "sqlalchemy", "checkout-service"]
    },
    {
        "id": "INC-2024-0715",
        "date": "2024-07-15 19:30 UTC",
        "service": "notification-worker",
        "title": "WebSocket Connection Leak Exhausting File Descriptors (EMFILE)",
        "error_logs": """[notification-worker] 2024-07-15 19:28:10 ERROR uvicorn.error: [Errno 24] Too many open files
[notification-worker] 2024-07-15 19:28:14 CRITICAL socket.py:34 - OSError: [Errno 24] Too many open files
[notification-worker] 2024-07-15 19:29:00 ERROR server.py:108 - Failed to accept new incoming WebSocket connections. 65,535 file descriptors in use.""",
        "root_cause": "Client disconnect heartbeat ping was disabled on the mobile gateway, preventing TCP keep-alive termination and stranding 60,000 dead sockets indefinitely.",
        "fix_steps": "1. Increased system ulimit open files limit from 65,535 to 262,144.\n2. Enabled aggressive WebSocket ping interval of 30s with 10s pong timeout in FastAPI app.\n3. Restarted notification-worker pods in rolling wave.",
        "time_to_resolve": "18 minutes",
        "who_fixed_it": "Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["websockets", "file-descriptors", "emfile", "socket-leak", "notification-worker"]
    },
    {
        "id": "INC-2024-0728",
        "date": "2024-07-28 08:50 UTC",
        "service": "payment-gateway",
        "title": "Duplicate Transaction Processing on Webhook Retry (Idempotency Key Collision)",
        "error_logs": """[payment-gateway] 2024-07-28 08:48:19 WARN payments/processor.py:112 - Detected concurrent webhook delivery for charge_id=ch_99218274
[payment-gateway] 2024-07-28 08:48:20 ERROR db/ledger.py:59 - psycopg2.IntegrityError: duplicate key value violates unique constraint "idx_tx_idempotency_key"
[payment-gateway] 2024-07-28 08:49:00 ERROR views.py:145 - Double capture prevented by DB constraint, but HTTP 500 returned causing upstream to retry forever!""",
        "root_cause": "The webhook receiver caught IntegrityError on idempotency collision and returned HTTP 500 instead of HTTP 200 with the cached original response, causing the payment partner to hammer our endpoint every 2 seconds.",
        "fix_steps": "1. Handled IntegrityError in webhook handler to return HTTP 200 OK with original payment receipt payload.\n2. Implemented distributed Redis mutex lock on idempotency key before initiating processing.\n3. Notified finance of 0 duplicate customer charges.",
        "time_to_resolve": "31 minutes",
        "who_fixed_it": "Elena Rostova (Payments Lead)",
        "fix_status": "SUCCESS",
        "tags": ["idempotency", "duplicate-transaction", "webhooks", "redis-lock", "payment-gateway"]
    },
    {
        "id": "INC-2024-0803",
        "date": "2024-08-03 16:00 UTC",
        "service": "settlement-pipeline",
        "title": "AWS S3 Bucket Permission Policy Change Breaking Audit CSV Exports",
        "error_logs": """[settlement-pipeline] 2024-08-03 15:58:12 ERROR botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the PutObject operation: Access Denied
[settlement-pipeline] 2024-08-03 15:58:30 CRITICAL exporter/s3.py:88 - Failed to upload daily settlement batch 20240803.csv to s3://northwind-settlement-reports/
[monitoring] 2024-08-03 15:59:00 ALERT Banking reconciliation report failed to generate.""",
        "root_cause": "A security hardening script applied a default bucket policy requiring aws:PrincipalArn to match an obsolete IAM role name, rejecting the Kubernetes settlement-worker service account.",
        "fix_steps": "1. Updated S3 bucket policy JSON to whitelist IRSA role arn:aws:iam::123456789012:role/settlement-worker-role.\n2. Reran failed export task using airflow trigger_dag settlement_export.\n3. Verified successful S3 PutObject and banking ACK.",
        "time_to_resolve": "20 minutes",
        "who_fixed_it": "Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["s3", "iam", "access-denied", "permissions", "settlement-pipeline"]
    },
    {
        "id": "INC-2024-0810",
        "date": "2024-08-10 11:15 UTC",
        "service": "auth-api",
        "title": "Stale Redis Cache Serving Expired JWT Signatures After Key Rotation",
        "error_logs": """[auth-api] 2024-08-10 11:13:05 ERROR jwt.exceptions.InvalidSignatureError: Signature verification failed
[auth-api] 2024-08-10 11:13:20 WARN auth_middleware.py:82 - JWT signature rejected for user_id=usr_44921. JWKS key_id=kid_2024_08_a not found in cached keyset.
[auth-api] 2024-08-10 11:14:00 CRITICAL 401 Unauthorized spike to 94% across all incoming API traffic.""",
        "root_cause": "JWKS public key rotation completed in Vault, but auth-api instances cached the old JWKS keyset in Redis with an immutable 24-hour TTL without key eviction.",
        "fix_steps": "1. Flushed cached JWKS keys in Redis: redis-cli DEL cache:jwks_keyset.\n2. Configured auth-api to re-fetch JWKS on kid miss with a 5-second rate limiter to prevent cache stampedes.\n3. User authentication immediately recovered to 100% success.",
        "time_to_resolve": "12 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["jwt", "jwks", "cache", "redis", "auth-api"]
    },
    {
        "id": "INC-2024-0818",
        "date": "2024-08-18 22:40 UTC",
        "service": "checkout-service",
        "title": "Zero-Byte ConfigMap Deployed in Payment Router via Broken Helm Pipeline",
        "error_logs": """[checkout-service] 2024-08-18 22:38:10 ERROR config_loader.py:34 - FileNotFoundError: Configuration file /etc/northwind/router.yaml is empty or missing!
[checkout-service] 2024-08-18 22:38:12 CRITICAL main.py:19 - SystemExit: Fatal configuration error on startup.
[k8s-events] 2024-08-18 22:39:00 Pod checkout-router-88bf9-xklm1 CrashLoopBackOff: back-off 5m0s restarting failed container""",
        "root_cause": "A GitHub Actions pipeline variable typo `$ROUTER_CONFIG_YAML` evaluated to empty string during envsubst, producing a 0-byte Kubernetes ConfigMap that replaced production router config.",
        "fix_steps": "1. Rolled back deployment to previous revision: kubectl rollout undo deployment/checkout-router.\n2. Verified router.yaml mounted with valid routing rules.\n3. Added CI pre-deploy assertion verifying config file byte size > 100 bytes before helm upgrade.",
        "time_to_resolve": "15 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["kubernetes", "configmap", "helm", "crashloop", "checkout-service"]
    },
    {
        "id": "INC-2024-0822",
        "date": "2024-08-22 17:15 UTC",
        "service": "fraud-detector",
        "title": "Elasticsearch Unassigned Shards Causing Cluster RED Status",
        "error_logs": """[fraud-detector] 2024-08-22 17:13:00 ERROR elasticsearch.exceptions.ConnectionError: N/A: ('Connection lost', ConnectionResetError(104, 'Connection reset by peer'))
[monitoring] 2024-08-22 17:13:30 CRITICAL es-cluster health: RED. 12 unassigned primary shards on index fraud_events_2024_08.
[fraud-detector] 2024-08-22 17:14:00 ERROR search.py:90 - SearchPhaseExecutionException: all shards failed.""",
        "root_cause": "Data node data-es-02 ran out of disk threshold (watermark 85%), triggering shard allocation locks and leaving 12 shards unassigned when the pod was rescheduled.",
        "fix_steps": "1. Freed disk space by deleting snapshot temp files and indices older than 90 days.\n2. Reset allocation threshold: PUT _cluster/settings {'transient': {'cluster.routing.allocation.enable': 'all'}}.\n3. Shard recovery completed in 10 minutes, returning cluster to GREEN.",
        "time_to_resolve": "29 minutes",
        "who_fixed_it": "Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["elasticsearch", "shards", "disk-watermark", "fraud-detector"]
    },
    {
        "id": "INC-2024-0825",
        "date": "2024-08-25 14:00 UTC",
        "service": "payment-gateway",
        "title": "FAILED REMEDIATION: Increasing gRPC Timeout to 60s Caused Upstream Thread Starvation",
        "error_logs": """[payment-gateway] 2024-08-25 13:58:00 ERROR grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
    status = StatusCode.DEADLINE_EXCEEDED
    details = "Deadline Exceeded"
>
[api-gateway] 2024-08-25 13:59:10 CRITICAL uvicorn.workers: Worker failed to boot. Active connections hit max_workers limit (1000/1000). All threads stuck waiting 60s for payment-gateway!""",
        "root_cause": "When bank acquirer had a 15-second latency spike, engineer increased gRPC client timeout from 3s to 60s. Instead of resolving failures, this pinned web server threads for a full minute, exhausting connection pools across all upstream microservices.",
        "fix_steps": "FAILED ATTEMPT: Increased timeout to 60s.\nACTUAL FIX: Reverted gRPC timeout to strict 2.5s with fail-fast circuit breaker. Enabled Hedged Requests (duplicate request dispatched after 800ms) to bypass slow acquirer nodes.",
        "time_to_resolve": "55 minutes",
        "who_fixed_it": "Devon Reed (Junior DevOps) & Elena Rostova (Payments Lead)",
        "fix_status": "FAILED",
        "failed_reason": "Increasing RPC timeouts masked downstream slowness, holding connections open 20x longer and cascading thread starvation into all upstream callers.",
        "tags": ["grpc", "timeout", "cascading-failure", "failed-fix", "payment-gateway"]
    },
    {
        "id": "INC-2024-0829",
        "date": "2024-08-29 09:30 UTC",
        "service": "checkout-service",
        "title": "PostgreSQL Connection Pool Exhaustion from Leaky Async Coroutines",
        "error_logs": """[checkout-service] 2024-08-29 09:28:40 ERROR asyncpg.exceptions.TooManyConnectionsError: sorry, too many clients already
[checkout-service] 2024-08-29 09:29:01 CRITICAL pool.py:150 - asyncpg.pool.PoolAcquireTimeoutError: 10.00 seconds timeout acquiring connection from pool
[checkout-service] 2024-08-29 09:29:15 ERROR checkout/api.py:84 - 500 Internal Server Error returned to checkout frontend.""",
        "root_cause": "Async coroutines in customer loyalty points calculation spawned detached background tasks without acquiring connections via pool context manager, creating leaked connection handles.",
        "fix_steps": "1. Cleared idle backends in Postgres: SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query LIKE '%customer_loyalty%' AND state = 'idle';\n2. Refactored loyalty calculator to use async with pool.acquire() as conn: pattern.\n3. Added alert for asyncpg pool waiting count > 10.",
        "time_to_resolve": "22 minutes",
        "who_fixed_it": "Marcus Vance (Staff Infra)",
        "fix_status": "SUCCESS",
        "tags": ["postgres", "asyncpg", "connection-pool", "leak", "checkout-service"]
    },
    {
        "id": "INC-2024-0905",
        "date": "2024-09-05 18:20 UTC",
        "service": "settlement-pipeline",
        "title": "Kafka Consumer Partition Rebalance Loop in Settlement Ingestion",
        "error_logs": """[settlement-pipeline] 2024-09-05 18:18:20 WARN kafka.coordinator.consumer: Consumer consumer-1 marked dead due to max.poll.interval.ms exceeded
[settlement-pipeline] 2024-09-05 18:18:45 ERROR kafka.consumer.group: CommitFailedException: Commit cannot be completed since the group has already rebalanced and assigned the partitions to another member.
[settlement-pipeline] 2024-09-05 18:19:10 CRITICAL Constant partition rebalancing stopping message ingestion completely!""",
        "root_cause": "A single giant merchant batch of 50,000 transactions took 8 minutes to process synchronously, exceeding max.poll.interval.ms (300,000ms = 5 mins) and triggering an endless consumer group rebalance storm.",
        "fix_steps": "1. Increased max.poll.interval.ms to 900,000ms (15 mins) and reduced max.poll.records from 500 to 50.\n2. Delegated heavy batch calculation to a decoupled background worker pool with async acknowledge.\n3. Rebalance storm stopped immediately, throughput normalized.",
        "time_to_resolve": "30 minutes",
        "who_fixed_it": "Sarah Chen (Senior SRE)",
        "fix_status": "SUCCESS",
        "tags": ["kafka", "rebalance", "poll-interval", "settlement-pipeline"]
    }
]

# 3 one-click sample incidents for the UI
SAMPLE_INCIDENTS = [
    {
        "id": "sample-1",
        "name": "Postgres Pool Exhaustion (Checkout)",
        "service": "checkout-service",
        "alert": "P1 ALERT: Checkout Service HTTP 500 Spike & Connection Pool Starvation",
        "logs": """[checkout-service] ERROR django.db.utils.OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections
[checkout-service] CRITICAL pool_manager.py:88 - ConnectionPoolExhausted: Pool max_connections=200 reached. Active: 200, Waiting: 185.
Traceback (most recent call last):
  File "apps/checkout/views.py", line 112, in process_cart
    with db.transaction.atomic():
  File "django/db/backends/base/base.py", line 219, in get_new_connection
    return Database.connect(**conn_params)
OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections"""
    },
    {
        "id": "sample-2",
        "name": "Payment Gateway 429 Rate Limit (Stripe/Adyen)",
        "service": "payment-gateway",
        "alert": "P1 ALERT: Payment Gateway Card Processing Failure Rate > 45%",
        "logs": """[payment-gateway] WARN providers/stripe_client.py:145 - 429 Client Error: Too Many Requests for url: https://api.stripe.com/v1/payment_intents
[payment-gateway] ERROR gateway/orchestrator.py:210 - UpstreamPaymentProviderRateLimit: Rate limit quota exceeded (100 req/sec limit).
[payment-gateway] ERROR gateway/views.py:76 - 503 Service Unavailable returned to client token=tok_flash_sale_492
[payment-gateway] CRITICAL circuit_breaker.py:102 - Stripe primary gateway failure rate 52% exceeded threshold!"""
    },
    {
        "id": "sample-3",
        "name": "Kafka Consumer Lag Spike (Settlement)",
        "service": "settlement-pipeline",
        "alert": "P2 ALERT: Settlement Consumer Lag > 90,000 Records & Worker Stalled",
        "logs": """[settlement-pipeline] ERROR kafka_consumer.py:102 - RecordProcessingException in partition 3 offset 9028114
Traceback (most recent call last):
  File "workers/settlement.py", line 45, in handle_message
    amount_cents = int(record['payload']['transaction_amount'])
ValueError: invalid literal for int() with base 10: 'null'
[settlement-pipeline] CRITICAL monitoring/lag.py:19 - Consumer group 'settlement-workers' lag exceeded 92,400 records! Partition 3 progress 0 msg/sec."""
    }
]

# 3-step demo scenarios for hackathon judges
DEMO_SCENARIOS = [
    {
        "step": 1,
        "title": "Step 1: New Alert - Postgres Pool Exhaustion",
        "description": "Examine a new Postgres connection pool alert. Without memory, the agent offers generic advice ('scale pods, restart database'). With Hindsight memory, it pinpoints previous connection leaks in checkout background threads and provides the exact pg_terminate_backend SQL query used by Marcus Vance.",
        "incident": SAMPLE_INCIDENTS[0]
    },
    {
        "step": 2,
        "title": "Step 2: Cross-Symptom Recall - Cart 504 Timeout",
        "description": "The alert manifests under completely different symptoms: 'HTTP 504 Gateway Timeout on Cart API'. Hindsight connects this symptom to past database connection pool wait contention (INC-2024-0418) rather than an API network issue!",
        "incident": {
            "id": "demo-step-2",
            "name": "Cart API 504 Gateway Timeout",
            "service": "checkout-service",
            "alert": "P1 ALERT: Cart API Latency > 30s & Influx of HTTP 504 Gateway Timeouts",
            "logs": """[api-gateway] ERROR upstream_connect_timeout: upstream 10.0.4.18:8000 timed out (504 Gateway Timeout)
[checkout-service] WARN db_pool: pool acquire wait time exceeded 30,000ms. Available connections: 0 / 180.
[checkout-service] ERROR views.py:221 - User checkout checkout_token=ch_99214 failed after 30s timeout waiting for DB handle."""
        }
    },
    {
        "step": 3,
        "title": "Step 3: Learning from Failed Remediations",
        "description": "See the feedback loop in action: A previous on-call engineer blindly rebooted PostgreSQL (INC-2024-0301) and caused a catastrophic thundering herd crash. Hindsight remembers this failure and explicitly warns the engineer NOT to hard-reboot the database, recommending PgBouncer throttling instead.",
        "incident": {
            "id": "demo-step-3",
            "name": "Critical Database Connection Saturation",
            "service": "checkout-service",
            "alert": "P0 CRITICAL: Database Connections 99% Saturated Across All Clusters",
            "logs": """[checkout-service] CRITICAL pool_manager.py:88 - ConnectionPoolExhausted: Pool max_connections=200 reached.
[postgres-rds] WARNING: 198 of 200 connection slots in use. Remaining slots reserved for superuser.
[oncall-slack] DevOps asking: 'Should we just do a hard reboot on the RDS primary right now?'"""
        }
    }
]
