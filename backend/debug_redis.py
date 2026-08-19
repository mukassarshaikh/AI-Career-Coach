"""
Quick diagnostic script to test Redis/Arq enqueue+dequeue pipeline.

Run from: c:\projects\POC\AI-Career-Coach\backend
  python debug_redis.py
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    from app.core.config import settings
    from arq.connections import RedisSettings, create_pool

    print(f"REDIS_URL = {settings.redis_url!r}")
    print(f"REDIS_URL length = {len(settings.redis_url)}")
    print(f"Starts with rediss:// = {settings.redis_url.startswith('rediss://')}")

    rs = RedisSettings.from_dsn(settings.redis_url)
    print(f"\nRedisSettings = {rs}")
    print(f"  host={rs.host!r}")
    print(f"  port={rs.port!r}")
    print(f"  ssl={rs.ssl!r}")
    print(f"  database={rs.database!r}")
    print(f"  username={rs.username!r}")
    print(f"  password={'***' if rs.password else None}")

    print("\nConnecting to Redis...")
    pool = await create_pool(rs)
    print("Connected! Pinging...")
    pong = await pool.ping()
    print(f"Ping result: {pong}")

    # Check default queue name
    print(f"\nDefault queue name: {pool.default_queue_name!r}")

    # Check what's currently in the queue
    queued = await pool.zrange(pool.default_queue_name, start=0, end=-1, withscores=True)
    print(f"Current queue contents ({len(queued)} jobs):")
    for job_id, score in queued:
        print(f"  job_id={job_id}, score={score}")

    # Check all keys matching arq:*
    keys = await pool.keys("arq:*")
    print(f"\nAll arq:* keys ({len(keys)}):")
    for k in keys:
        print(f"  {k}")

    # Try enqueue a test job
    print("\n--- Enqueue test ---")
    job = await pool.enqueue_job("parse_resume", "test-uuid-00000000")
    if job:
        print(f"Enqueued job: id={job.job_id}")
        status = await job.status()
        print(f"Job status: {status}")
    else:
        print("enqueue_job returned None — job already exists?")

    # Re-check queue
    queued = await pool.zrange(pool.default_queue_name, start=0, end=-1, withscores=True)
    print(f"\nQueue after enqueue ({len(queued)} jobs):")
    for job_id, score in queued:
        print(f"  job_id={job_id}, score={score}")

    await pool.close()
    print("\nDone.")

asyncio.run(main())
