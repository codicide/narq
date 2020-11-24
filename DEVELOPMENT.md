
# Development

## Running Tests

Some tests require an open `redis` instance running on localhost:6379
The simplest method is to run a docker container for development purposes.

```bash
docker run --rm --name narq-redis -p 127.0.0.1:6379:6379 -d redis:alpine
make all
```
