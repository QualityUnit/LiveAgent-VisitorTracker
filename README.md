# LiveAgent VisitorTracker

this is a very simple service, that takes tracking request and saves data to Redis and ElasticSearch.

Visitor sessions are listed in a Redis list, and the session data is stored in Redis hashes that expire automatically.
Visitor lists expire after 2 minutes, at a time always 2 lists exists - list for the current minute and the previous minute.
Page visits are stored in Elasticsearch index, each day a new index is used. 

## Configuration
environment variables:
- `REDIS_URL`:
  - `redis://redis:6379`
  - `redis://[[username]:[password]]@localhost:6379/0` creates a TCP socket connection. See more at: https://www.iana.org/assignments/uri-schemes/prov/redis 
  - `rediss://[[username]:[password]]@localhost:6379/0` creates a SSL wrapped TCP socket connection. See more at: https://www.iana.org/assignments/uri-schemes/prov/rediss
  - `unix://[username@]/path/to/socket.sock?db=0[&password=password]` creates a Unix Domain Socket connection.
- `ELASTICSEARCH_URL` e.g.: `http://elasticsearch:9200` (multiple hosts can be specified, separated by `,` comma)
- `ELASTIC_USER` & `ELASTIC_PASS` Basic auth credentials for Elasticsearch: 
- `ELASTIC_CA`: path to CA certificate file for Elasticsearch
- `ELASTIC_APIKEY_ID` and `ELASTIC_APIKEY_KEY` apikey auth credentials for Elasticsearch 
- `ELASTIC_TIMEOUT` Elasticsearch request timeout


## Usage
send GET request with appropriate tracking query params to following paths:
- `/update_visit_expire/{session}/{tenantId}/{browserId}`
- `/track_button_impression/{tenantId}`
- `/track_visit/{tenantId}`
