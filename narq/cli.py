"""All functions to support CLI actions."""
import importlib
import os
import sys

import click

from .version import VERSION
from .worker import WorkerSettings, check_health, run_worker

burst_help = 'Batch mode: exit once no jobs are found in any queue.'
health_check_help = 'Health Check: run a health check and exit.'
verbose_help = 'Enable verbose output.'


@click.command('narq')
@click.version_option(VERSION, '-V', '--version', prog_name='narq')
@click.argument('worker-pre-init', type=str, required=True)
@click.option('--burst/--no-burst', default=None, help=burst_help)
@click.option('--check', is_flag=True, help=health_check_help)
def cli(*, worker_pre_init: str, burst: bool, check: bool) -> None:
    """
    Job queues in python with asyncio and redis.

    CLI to run the narq worker.
    """
    sys.path.append(os.getcwd())
    module_name, func_name = worker_pre_init.split(":")
    module = importlib.import_module(module_name)
    worker_pre_init_func = getattr(module, func_name)
    worker_settings = worker_pre_init_func()

    if not isinstance(worker_settings, WorkerSettings):
        raise RuntimeError(f"{worker_pre_init} must return a WorkerSettings instance.")

    if check:
        exit(check_health(worker_settings))
    else:
        kwargs = {} if burst is None else {'burst': burst}
        run_worker(worker_settings, **kwargs)
