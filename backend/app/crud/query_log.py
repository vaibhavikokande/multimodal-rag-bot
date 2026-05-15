from sqlalchemy.ext.asyncio import AsyncSession
from app.models.query_log import QueryLog


async def create_query_log(db: AsyncSession, **kwargs):
    log = QueryLog(**kwargs)
    db.add(log)
    await db.commit()
    return log
