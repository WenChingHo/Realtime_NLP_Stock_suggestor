import asyncio
from numpy import broadcast
from pyppeteer import launch
import time
import re
from ABC_Crawler import Crawler
from my_websocket import RT_updater
from datetime import datetime
import websocket
import json

class cmoney_crawler(Crawler):
    def __init__(self, database):
        self.connect_to_db(database)

    def connect_to_db(self, database) -> None:
        super().connect_to_db(database)

    def crawl_data_to_db(self):
        pass

    async def get_data(self, browser, ticker):
        page = await browser.newPage()
        await page.goto(f'https://www.cmoney.tw/follow/channel/stock/{ticker}')
        await page.waitFor(".main-content")
        raw_html = await page.content()
        comments = re.findall("<div class=\"main-content\"(.*?)</div>[\S\s]*?title(.*?)\">", raw_html)

        for comment in comments:
            self.stream_data(ticker,comment)

        await page.close()
        # wait for comment to load
        
    async def start(self, tickers):
        while True:
            try:
                browser = await launch()
                tasks = [asyncio.create_task(self.get_data(browser, ticker)) for ticker in tickers]
                await asyncio.wait(tasks)
                await browser.close()
            except Exception as err:
                print(err)
            finally:
                await asyncio.sleep(30)

    def stream_data(self, ticker, comment):
        payload = {'message': comment[0], #爬到的留言
            'category': "chatmsg",
            "name": "CMoney",  #爬蟲的名字
            "time":comment[1]  #爬到的時間
            } 
        messenger = RT_updater(ticker, json.dumps(payload))
        messenger.run()
        messenger.close()

if __name__=="__main__":
    asyncio.get_event_loop().run_until_complete(cmoney_crawler("db,sqlite3").start(['2603', '2330']))
