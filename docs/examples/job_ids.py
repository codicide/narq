import asyncio

from narq import create_pool
from narq.connections import RedisSettings
from narq.worker import WorkerSettings

async def the_task(ctx):
    print('running the task with id', ctx['job_id'])

async def main():
    redis = await create_pool(RedisSettings())

    # no id, random id will be generated
    job1 = await redis.enqueue_job('the_task')
    print(job1)
    """
    >  <narq job 99edfef86ccf4145b2f64ee160fa3297>
    """

    # random id again, again the job will be enqueued and a job will be returned
    job2 = await redis.enqueue_job('the_task')
    print(job2)
    """
    >  <narq job 7d2163c056e54b62a4d8404921094f05>
    """

    # custom job id, job will be enqueued
    job3 = await redis.enqueue_job('the_task', _job_id='foobar')
    print(job3)
    """
    >  <narq job foobar>
    """

    # same custom job id, job will not be enqueued and enqueue_job will return None
    job4 = await redis.enqueue_job('the_task', _job_id='foobar')
    print(job4)
    """
    >  None
    """

def worker_pre_init() -> WorkerSettings:
    return WorkerSettings(
        functions=[the_task]
    )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
