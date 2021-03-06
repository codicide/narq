"""Module to manage all job classes."""
import asyncio
import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple

from aioredis import Redis

from .constants import default_queue_name, in_progress_key_prefix, job_key_prefix, result_key_prefix
from .utils import ms_to_datetime, poll, timestamp_ms

logger = logging.getLogger('narq.jobs')

Serializer = Callable[[Dict[str, Any]], bytes]
Deserializer = Callable[[bytes], Dict[str, Any]]


class JobStatus(str, Enum):
    """Enum of job statuses."""

    #: job is in the queue, time it should be run not yet reached
    deferred = 'deferred'
    #: job is in the queue, time it should run has been reached
    queued = 'queued'
    #: job is in progress
    in_progress = 'in_progress'
    #: job is complete, result is available
    complete = 'complete'
    #: job not found in any way
    not_found = 'not_found'


@dataclass
class JobDef:
    """Job definition dataclass."""

    function: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    job_try: int
    enqueue_time: datetime
    score: Optional[int]


@dataclass
class JobResult(JobDef):
    """Job result dataclass."""

    success: bool
    result: Any
    start_time: datetime
    finish_time: datetime
    job_id: Optional[str] = None


class Job:
    """Holds data a reference to a job."""

    __slots__ = 'job_id', '_redis', '_queue_name', '_deserializer'

    def __init__(
        self,
        job_id: str,
        redis: Redis,
        _queue_name: str = default_queue_name,
        _deserializer: Optional[Deserializer] = None,
    ):
        """Create a new job from a job ID."""
        self.job_id = job_id
        self._redis = redis
        self._queue_name = _queue_name
        self._deserializer = _deserializer

    async def result(self, timeout: Optional[float] = None, *, pole_delay: float = 0.5) -> Any:
        """Get the result of the job, including waiting if it's not yet available.

        If the job raised an exception, it will be raised here.

        :param timeout: maximum time to wait for the job result before raising ``TimeoutError``, will wait forever
        :param pole_delay: how often to poll redis for the job result
        """
        async for delay in poll(pole_delay):
            info = await self.result_info()
            if info:
                result = info.result
                if info.success:
                    return result
                elif isinstance(result, Exception):
                    raise result
                else:
                    raise SerializationError(result)
            if timeout is not None and delay > timeout:
                raise asyncio.TimeoutError()

    async def info(self) -> Optional[JobDef]:
        """All information on a job, including its result if it's available, does not wait for the result."""
        info: Optional[JobDef] = await self.result_info()
        if not info:
            v = await self._redis.get(job_key_prefix + self.job_id, encoding=None)
            if v:
                info = deserialize_job(v, deserializer=self._deserializer)
        if info:
            info.score = await self._redis.zscore(self._queue_name, self.job_id)
        return info

    async def result_info(self) -> Optional[JobResult]:
        """Information about the job result if available, does not wait for the result.

        Does not raise an exception even if the job raised one.
        """
        v = await self._redis.get(result_key_prefix + self.job_id, encoding=None)
        if v:
            return deserialize_result(v, deserializer=self._deserializer)
        else:
            return None

    async def status(self) -> JobStatus:
        """Status of the job."""
        if await self._redis.exists(result_key_prefix + self.job_id):
            return JobStatus.complete
        elif await self._redis.exists(in_progress_key_prefix + self.job_id):
            return JobStatus.in_progress
        else:
            score = await self._redis.zscore(self._queue_name, self.job_id)
            if not score:
                return JobStatus.not_found
            return JobStatus.deferred if score > timestamp_ms() else JobStatus.queued

    def __repr__(self) -> str:
        """Represent a job."""
        return f'<narq job {self.job_id}>'


class SerializationError(RuntimeError):
    """Error serializing object."""

    pass


class DeserializationError(SerializationError):
    """Error deserializing object."""

    pass


def serialize_job(
    function_name: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    job_try: Optional[int],
    enqueue_time_ms: int,
    *,
    serializer: Optional[Serializer] = None,
) -> Optional[bytes]:
    """Given job data, serialize it into bytes.

    :param function_name:
    :param args:
    :param kwargs:
    :param job_try:
    :param enqueue_time_ms:
    :param serializer:
    :return:
    """
    data = {'t': job_try, 'f': function_name, 'a': args, 'k': kwargs, 'et': enqueue_time_ms}
    if serializer is None:
        serializer = pickle.dumps
    try:
        return serializer(data)
    except Exception as e:
        raise SerializationError(f'unable to serialize job "{function_name}"') from e


def serialize_result(
    function: str,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
    job_try: int,
    enqueue_time_ms: int,
    success: bool,
    result: Any,
    start_ms: int,
    finished_ms: int,
    ref: str,
    *,
    serializer: Optional[Serializer] = None,
) -> Optional[bytes]:
    """Given job info, serializes them into bytes.

    :param function: The function name to call.
    :param args: tuple of args to pass to the function.
    :param kwargs: dict of kwargs to pass to the function.
    :param job_try: the number of tries the job took.
    :param enqueue_time_ms: time in milliseconds that the jobs was enqueued.
    :param success: flag indicating if the job was successful.
    :param result: result data from the job.
    :param start_ms: the unix timestamp of when the job started.
    :param finished_ms: the unix timestamp of when the job finished.
    :param ref: TODO: What is this thing?
    :param serializer: Optional serializer to use for serialization.  If not set, pickle is used.
    :return: bytes representing the passed data as a dict.
    """
    data = {
        't': job_try,
        'f': function,
        'a': args,
        'k': kwargs,
        'et': enqueue_time_ms,
        's': success,
        'r': result,
        'st': start_ms,
        'ft': finished_ms,
    }
    if serializer is None:
        serializer = pickle.dumps
    try:
        return serializer(data)
    except Exception:
        logger.warning('error serializing result of %s', ref, exc_info=True)

    # use string in case serialization fails again
    data.update(r='unable to serialize result', s=False)
    try:
        return serializer(data)
    except Exception:
        logger.critical('error serializing result of %s even after replacing result', ref, exc_info=True)
    return None


def deserialize_job(r: bytes, *, deserializer: Optional[Deserializer] = None) -> JobDef:
    """Given bytes, deserializes them into a JobDef.

    :param r: bytes to deserialize.
    :param deserializer: Optional serializer to use for deserialization.  If not set, pickle is used.
    :return: A JobDef.
    :raises DeserializationError: If bytes cannot be converted to JobDef.
    """
    if deserializer is None:
        deserializer = pickle.loads
    try:
        d = deserializer(r)
        return JobDef(
            function=d['f'],
            args=d['a'],
            kwargs=d['k'],
            job_try=d['t'],
            enqueue_time=ms_to_datetime(d['et']),
            score=None,
        )
    except Exception as e:
        raise DeserializationError('unable to deserialize job') from e


def deserialize_job_raw(
    r: bytes, *, deserializer: Optional[Deserializer] = None
) -> Tuple[str, Tuple[Any, ...], Dict[str, Any], int, int]:
    """Given bytes, deserializes them into a Tuple.

    :param r: bytes to deserialize.
    :param deserializer: Optional serializer to use for deserialization.  If not set, pickle is used.
    :return: A Tuple, holding the job information.
    :raises DeserializationError: If bytes cannot be converted to Tuple.
    """
    if deserializer is None:
        deserializer = pickle.loads
    try:
        d = deserializer(r)
        return d['f'], d['a'], d['k'], d['t'], d['et']
    except Exception as e:
        raise DeserializationError('unable to deserialize job') from e


def deserialize_result(r: bytes, *, deserializer: Optional[Deserializer] = None) -> JobResult:
    """Given bytes, deserializes them into a JobResult object.

    :param r: bytes to deserialize.
    :param deserializer: Optional serializer to use for deserialization.  If not set, pickle is used.
    :return: A JobResult object.
    :raises DeserializationError: If bytes cannot be converted to JobResult.
    """
    if deserializer is None:
        deserializer = pickle.loads
    try:
        d = deserializer(r)
        return JobResult(
            job_try=d['t'],
            function=d['f'],
            args=d['a'],
            kwargs=d['k'],
            enqueue_time=ms_to_datetime(d['et']),
            score=None,
            success=d['s'],
            result=d['r'],
            start_time=ms_to_datetime(d['st']),
            finish_time=ms_to_datetime(d['ft']),
        )
    except Exception as e:
        raise DeserializationError('unable to deserialize job result') from e
