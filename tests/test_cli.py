import logging
import sys

from click.testing import CliRunner
from narq.cli import cli
from narq.worker import WorkerSettings


async def foobar(ctx):
    return 42


def worker_start():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    return WorkerSettings(burst=True, functions=[foobar])


def test_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert result.output.startswith('Usage: narq [OPTIONS] WORKER_SETTINGS\n')


def test_run():
    runner = CliRunner()
    result = runner.invoke(cli, ['tests.test_cli:worker_start'])
    assert result.exit_code == 0
    assert 'Starting worker for 1 functions: foobar' in result.output


def test_check():
    runner = CliRunner()
    result = runner.invoke(cli, ['tests.test_cli:worker_start', '--check'])
    assert result.exit_code == 1
    assert 'Health check failed: no health check sentinel value found' in result.output
