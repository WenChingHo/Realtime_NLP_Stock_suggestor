import asyncio
from closing_price_crawler import closing_price_crawler
from udn_crawler import udn_crawler
from cmoney_crawler import cmoney_crawler
from pchome_crawler import pchome_crawler
from my_websocket import RT_updater

import asyncio

async def main():
    # Create crawler coroutine 
    crawlers = [
        closing_price_crawler("db.sqlite3").start(),
        udn_crawler("News.db").start(), 
        cmoney_crawler("Comment.db").start(),
        pchome_crawler("News.db").start()
    ]
    # Wrap coroutine into tasks to be passed into asyncio.wait()
    tasks = [asyncio.create_task(crawler) for crawler in crawlers]
    await asyncio.wait(tasks)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
