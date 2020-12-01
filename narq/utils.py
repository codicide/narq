"""Utility methods for narq."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from time import time
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Optional, Sequence, overload

logger = logging.getLogger('narq.utils')

if TYPE_CHECKING:
    from .typing import SecondsTimedelta


def as_int(f: float) -> int:
    """Convert a float to an int."""
    return int(round(f))


def timestamp_ms() -> int:
    """Get the current time in milliseconds."""
    return as_int(time() * 1000)


def to_unix_ms(dt: datetime) -> int:
    """Convert a datetime to epoch with milliseconds as int."""
    return as_int(dt.timestamp() * 1000)


def ms_to_datetime(unix_ms: int) -> datetime:
    """Convert unix timestamp in milliseconds to datetime."""
    return datetime.fromtimestamp(unix_ms / 1000, tz=timezone.utc)


def to_ms(td: Optional['SecondsTimedelta']) -> Optional[int]:
    """Convert a timedelta in seconds to milliseconds.  Returns None if None is passed."""
    if td is None:
        return td
    elif isinstance(td, timedelta):
        td = td.total_seconds()
    return as_int(td * 1000)


def to_seconds(td: 'SecondsTimedelta') -> float:
    """Convert a timedelta in seconds to seconds.  Returns None if None is passed."""
    if isinstance(td, timedelta):
        return td.total_seconds()
    return td


async def poll(step: float = 0.5) -> AsyncGenerator[float, None]:
    """Poll indefinitely every `step` seconds."""
    loop = asyncio.get_event_loop()
    start = loop.time()
    while True:
        before = loop.time()
        yield before - start
        after = loop.time()
        wait = max([0, step - after + before])
        await asyncio.sleep(wait)


DEFAULT_CURTAIL = 80


def truncate(s: str, length: int = DEFAULT_CURTAIL) -> str:
    """Truncate a string and add an ellipsis (three dots) to the end if it was too long.

    :param s: string to possibly truncate
    :param length: length to truncate the string to
    """
    if len(s) > length:
        s = s[: length - 1] + '…'
    return s


def args_to_string(args: Sequence[Any], kwargs: Dict[str, Any]) -> str:
    """Convert args to string.  Useful for printing.  Truncate the result to 80 characters max."""
    arguments = ''
    if args:
        arguments = ', '.join(map(repr, args))
    if kwargs:
        if arguments:
            arguments += ', '
        arguments += ', '.join(f'{k}={v!r}' for k, v in sorted(kwargs.items()))
    return truncate(arguments)
