import logging
import logging.config
import sys

from click.testing import CliRunner
from narq.cli import cli
from narq.worker import WorkerSettings


async def foobar(ctx):
    return 42


def worker_pre_init():
    log_level = "DEBUG"
    logging.config.dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'narq.standard': {'level': log_level, 'class': 'logging.StreamHandler', 'formatter': 'narq.standard'}
            },
            'formatters': {'narq.standard': {'format': '%(asctime)s: %(message)s', 'datefmt': '%H:%M:%S'}},
            'loggers': {'narq': {'handlers': ['narq.standard'], 'level': log_level}},
        }
    )
    return WorkerSettings(burst=True, functions=[foobar])


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert result.output.startswith('Usage: narq [OPTIONS] WORKER_SETTINGS\n')


def test_run():
    runner = CliRunner()
    result = runner.invoke(cli, ['tests.test_cli:worker_pre_init'])
    assert result.exit_code == 0
    assert 'Starting worker for 1 functions: foobar' in result.output


def test_check():
    runner = CliRunner()
    result = runner.invoke(cli, ['tests.test_cli:worker_pre_init', '--check'])
    assert result.exit_code == 1
    assert 'Health check failed: no health check sentinel value found' in result.output
