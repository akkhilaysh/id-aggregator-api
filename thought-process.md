## Project
Building an implementation of an API that aggregates unique ids consumed via a GET request. Record the count unique ids in a log file.

Take any endpoints recieved and trigger POST call for every endpoint and record response in log file.

---

### General Program Flow
When the program starts, it kicks off a background job that waits for 60 seconds. During that time, any request to `GET /api/verve/accept` saves the provided id (and an optional endpoint) in our centralised DB (Redis). When the 60 second timer is up, the 60 second loop/job grabs all unique IDs from Redis, totals them, and either logs that number or sends it to RabbitMQ. If any endpoints were collected, the job also makes a POST to each one with the final count and logs the response in a log file called `unique_id_capture.log`. Finally, it clears the stored IDs so the process can repeat every minute with a fresh set.

---

### Why FastAPI?
Easy to setup & Handles High Throughput

- I chose FastAPI for the REST service, due to its simplicity and speed.
- Used Docker to containerize the app for easier scaling.
- Docker Compose so that all services are defined and spun up using one file in one file: Compose allows me to specify each required service (redis, rabbitMQ, FastApi) in a single yaml file.


### Extension 1:
Problem: Multiple instances of the API could receive the same id at nearly the same time, leading to double-counting.

Solution: Handling de-duplication due to concurrent writes of the same id: Add a centralised dataset, Redis. 
  - **Why Redis**: 
Redis is fast and can handle write heavy 10k requests per second as mentioned in the base requirements.
Leveraging set operations in Redis using r.sadd() ensures duplicates aren’t counted twice since we share it as a centralised db

### Extension 2:
If RabbitMQ is not setup or connected then the unique id count every minute will get published to a log file named unique_id_capture.log. If RabbitMQ is available, it sends the aggregated counts there instead.

---

### Next
1. Database credentials or RabbitMQ secrets can be secured using environment variables, secret managers, or vaults. Make sure to avoid committing sensitive info directly in version control.
2. Split the code into separate modules (e.g., aggregator.py for the background aggregation logic, rabbitmq.py for connecting to RabbitMQ, app.py for the FastAPI routes).  
3. Add Unit tests: This makes the code easier to maintain and test.
