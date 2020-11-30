
# Development

## Setup

1. Create and activate a virtualenv with Python 3.6 or higher.
2. Clone this repo into the new virtualenv directory
3. `pip install -e .`


## Running Tests

Some tests require an open `redis` instance running on localhost:6379
The simplest method is to run a docker container for development purposes.

```bash
docker run --rm --name narq-redis -p 127.0.0.1:6379:6379 -d redis:alpine
make all
```
