import asyncio, os 
from dotenv import load_dotenv 
from sqlalchemy.ext.asyncio import create_async_engine 
from sqlalchemy import text 
load_dotenv() 
async def check(): 
    engine = create_async_engine(os.environ['DATABASE_URL']) 
    async with engine.connect() as conn: 
        count = await conn.execute(text('SELECT COUNT(*) FROM market_skill_reference')) 
        print('Seed row count:', count.scalar()) 
        roles = await conn.execute(text('SELECT DISTINCT role_title FROM market_skill_reference LIMIT 10')) 
        print('Sample roles:', [r[0] for r in roles]) 
    await engine.dispose() 
asyncio.run(check()) 
