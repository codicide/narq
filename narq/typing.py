"""Module to hold classes used for type hints."""
import sys
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Set, Union

if sys.version_info >= (3, 8):
    from typing import Protocol, Literal
else:
    from typing_extensions import Protocol, Literal

__all__ = (
    'OptionType',
    'WeekdayOptionType',
    'WEEKDAYS',
    'SecondsTimedelta',
    'WorkerCoroutine',
    'StartupShutdown',
)


if TYPE_CHECKING:
    from .worker import Function  # noqa F401
    from .cron import CronJob  # noqa F401

OptionType = Union[None, Set[int], int]
WEEKDAYS = 'mon', 'tues', 'wed', 'thurs', 'fri', 'sat', 'sun'
WeekdayOptionType = Union[OptionType, Literal['mon', 'tues', 'wed', 'thurs', 'fri', 'sat', 'sun']]
SecondsTimedelta = Union[int, float, timedelta]


# Originally this was defined as a protocol, which would be nice, but there are limitations with those and loosely
# defined method signatures.
# https://github.com/python/mypy/issues/9560
# https://github.com/python/mypy/issues/5876
WorkerCoroutine = Callable[..., Awaitable[Any]]


class StartupShutdown(Protocol):
    """Protocol for a startup or shutdown method.

    Requires the context and then any addtional args.
    """

    __qualname__: str

    async def __call__(self, ctx: Dict[Any, Any]) -> Any:  # pragma: no cover
        """Call the method."""
        pass
