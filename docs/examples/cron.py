from narq import cron
from narq.worker import WorkerSettings

async def run_regularly(ctx):
    print('run foo job at 9.12am, 12.12pm and 6.12pm')


def worker_pre_init() -> WorkerSettings:
    return WorkerSettings(
        cron_jobs=[
            cron(run_regularly, hour={9, 12, 18}, minute=12)
        ]
    )
