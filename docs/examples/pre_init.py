from narq.worker import WorkerSettings
import logging
import sys


def worker_pre_init() -> WorkerSettings:
    # Configure logging for the worker
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # Create worker settings, and return it.
    return WorkerSettings(
        functions=[]
    )
