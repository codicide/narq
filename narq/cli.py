"""All functions to support CLI actions."""
import logging.config
import os
import sys
from typing import TYPE_CHECKING, cast

import click
from pydantic.utils import import_string

from .logs import default_log_config
from .version import VERSION
from .worker import check_health, run_worker

if TYPE_CHECKING:
    from .typing import WorkerSettingsType

burst_help = 'Batch mode: exit once no jobs are found in any queue.'
health_check_help = 'Health Check: run a health check and exit.'
verbose_help = 'Enable verbose output.'


@click.command('narq')
@click.version_option(VERSION, '-V', '--version', prog_name='narq')
@click.argument('worker-settings', type=str, required=True)
@click.option('--burst/--no-burst', default=None, help=burst_help)
@click.option('--check', is_flag=True, help=health_check_help)
@click.option('-v', '--verbose', is_flag=True, help=verbose_help)
def cli(*, worker_settings: str, burst: bool, check: bool, verbose: bool) -> None:
    """
    Job queues in python with asyncio and redis.

    CLI to run the narq worker.
    """
    sys.path.append(os.getcwd())
    worker_settings_ = cast('WorkerSettingsType', import_string(worker_settings))
    logging.config.dictConfig(default_log_config(verbose))

    if check:
        exit(check_health(worker_settings_))
    else:
        kwargs = {} if burst is None else {'burst': burst}
        run_worker(worker_settings_, **kwargs)
