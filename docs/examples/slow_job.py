import asyncio

from narq import create_pool
from narq.connections import RedisSettings
from narq.worker import WorkerSettings

async def the_task(ctx):
    await asyncio.sleep(5)

async def main():
    redis = await create_pool(RedisSettings())
    await redis.enqueue_job('the_task')

def worker_pre_init() -> WorkerSettings:
    return WorkerSettings(
        functions=[the_task]
    )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
