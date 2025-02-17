## Setup - Getting Started:

### Run using Docker

#### Run the App and hit endpoint

```bash
git clone https://github.com/akkhilaysh/id-aggregator-api.git
```

```bash
cd verve-core-api
```

```bash
curl "http://localhost:8000/api/verve/accept?id=123&endpoint=http://example.com"
```

#### Monitor logs, db and stream

#### 1. Logs
```bash
docker-compose exec fastapi bash

ls

cat unique_id_capture.log
```

```bash
exit
```

##### 2. Redis
```bash

docker-compose exec redis bash

redis-cli

KEYS *

SMEMBERS unique_ids_for_current_minute
```

```bash
exit
```

##### 3. Stream (rabbit-mq)
```bash
docker-compose logs rabbitmq

docker-compose exec rabbitmq bash

rabbitmqctl list_queues name messages
```

```bash
exit
```
