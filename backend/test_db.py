import asyncio
from db.connection import database

async def test_connection():

    collections = await database.list_collection_names()

    print("MongoDB Connected ✅")
    print(collections)

asyncio.run(test_connection())