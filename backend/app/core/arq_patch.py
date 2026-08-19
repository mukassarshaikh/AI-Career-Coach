"""
arq_patch.py — Runtime compatibility patch for Arq 0.26.1 with redis-py 4.2+/5.x.

In redis-py (redis.asyncio), command methods on a Pipeline instance (such as
`pipe.exists()` and `pipe.zscore()`) buffer the command and return the Pipeline object.
Awaiting those returned objects (`await pipe.exists()`) triggers `Pipeline.__await__()`,
which calls `pipe.execute()` and returns a list containing the result (e.g., `[0]`).

In Python, `bool([0])` evaluates to `True`!
This caused two critical bugs in standard Arq 0.26.1:
1. `enqueue_job()`: `if await pipe.exists(...)` evaluated `if [0]: return None`,
   causing `enqueue_job()` to return `None` (failed enqueue).
2. `start_jobs()`: `if ongoing_exists or not score:` evaluated `if [0] or not score:`,
   causing the worker to think every enqueued job was "already running elsewhere"
   and silently skip it.

This patch fixes both issues by using direct client calls on `self` / `self.pool`
inside the `watch` transaction block.
"""

import logging
from arq.connections import ArqRedis, job_key_prefix, result_key_prefix, to_ms, timestamp_ms, to_unix_ms, serialize_job, Job
from arq.worker import Worker, in_progress_key_prefix, ResponseError, WatchError

from uuid import uuid4

logger = logging.getLogger(__name__)

_patched = False


def apply_arq_patch():
    global _patched
    if _patched:
        return
    _patched = True

    # 1. Patch ArqRedis.enqueue_job
    original_enqueue = ArqRedis.enqueue_job

    async def patched_enqueue_job(
        self: ArqRedis,
        function: str,
        *args,
        _job_id=None,
        _queue_name=None,
        _defer_until=None,
        _defer_by=None,
        _expires=None,
        _job_try=None,
        **kwargs,
    ):
        if _queue_name is None:
            _queue_name = self.default_queue_name
        job_id = _job_id or uuid4().hex
        job_key = job_key_prefix + job_id
        if _defer_until and _defer_by:
            raise RuntimeError("use either 'defer_until' or 'defer_by' or neither, not both")

        defer_by_ms = to_ms(_defer_by)
        expires_ms = to_ms(_expires)

        async with self.pipeline(transaction=True) as pipe:
            await pipe.watch(job_key)
            # Use direct client call self.exists instead of await pipe.exists
            if await self.exists(job_key, result_key_prefix + job_id):
                await pipe.reset()
                return None

            enqueue_time_ms = timestamp_ms()
            if _defer_until is not None:
                score = to_unix_ms(_defer_until)
            elif defer_by_ms:
                score = enqueue_time_ms + defer_by_ms
            else:
                score = enqueue_time_ms

            expires_ms = expires_ms or score - enqueue_time_ms + self.expires_extra_ms

            job = serialize_job(function, args, kwargs, _job_try, enqueue_time_ms, serializer=self.job_serializer)
            pipe.multi()
            pipe.psetex(job_key, expires_ms, job)
            pipe.zadd(_queue_name, {job_id: score})
            try:
                await pipe.execute()
            except WatchError:
                return None
        return Job(job_id, redis=self, _queue_name=_queue_name, _deserializer=self.job_deserializer)

    ArqRedis.enqueue_job = patched_enqueue_job

    # 2. Patch Worker.start_jobs
    async def patched_start_jobs(self: Worker, job_ids: list[bytes]) -> None:
        for job_id_b in job_ids:
            await self.sem.acquire()

            if self.job_counter >= self.max_jobs:
                self.sem.release()
                return None

            self.job_counter = self.job_counter + 1

            job_id = job_id_b.decode()
            in_progress_key = in_progress_key_prefix + job_id
            async with self.pool.pipeline(transaction=True) as pipe:
                await pipe.watch(in_progress_key)
                # Use direct client calls self.pool.exists and self.pool.zscore instead of await pipe.exists/zscore
                ongoing_exists = await self.pool.exists(in_progress_key)
                score = await self.pool.zscore(self.queue_name, job_id)
                if ongoing_exists or not score:
                    self.job_counter = self.job_counter - 1
                    self.sem.release()
                    logger.debug('job %s already running elsewhere', job_id)
                    continue

                pipe.multi()
                pipe.psetex(in_progress_key, int(self.in_progress_timeout_s * 1000), b'1')
                try:
                    await pipe.execute()
                except (ResponseError, WatchError):
                    self.job_counter = self.job_counter - 1
                    self.sem.release()
                    logger.debug('multi-exec error, job %s already started elsewhere', job_id)
                else:
                    t = self.loop.create_task(self.run_job(job_id, int(score)))
                    t.add_done_callback(lambda _: self._release_sem_dec_counter_on_complete())
                    self.tasks[job_id] = t

    Worker.start_jobs = patched_start_jobs
    logger.info("Arq 0.26.1 redis-py pipeline compatibility patch applied successfully.")
