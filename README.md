# LiveAgent VisitorTracker

this is a very simple service, that takes tracking request and saves data to Redis and ElasticSearch.

Visitor sessions are listed in a Redis list, and the session data is stored in Redis hashes that expire automatically.
Visitor lists expire after 2 minutes, at a time always 2 lists exists - list for the current minute and the previous minute.
Page visits are stored in Elasticsearch index, each day a new index is used. 

## Configuration
environment variables:
- `REDIS_URL` e.g.: `redis://redis:6379`
- `ELASTICSEARCH_URL` e.g.: `http://elasticsearch:9200`


## Usage
send GET request with appropriate tracking query params to following paths:
- `/update_visit_expire/{session}/{tenantId}/{browserId}`
- `/track_button_impression/{tenantId}`
- `/track_visit/{tenantId}`
