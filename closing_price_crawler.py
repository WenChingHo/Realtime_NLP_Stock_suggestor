
import re
import pickle
import json
from datetime import datetime, timedelta
from ABC_Crawler import Crawler
import asyncio
import aiohttp


class closing_price_crawler(Crawler):
    def __init__(self, database):
        self.connect_to_db(database)
        self.data = 0

    def connect_to_db(self, database) -> None:
        super().connect_to_db(database)

    def get_last_data_date(self):
        week_of_day = datetime.today().weekday()
        days_to_subtract = 0
        if week_of_day == 0:
            days_to_subtract = 3
        elif week_of_day == 6: 
            days_to_subtract = 2
        else:
            days_to_subtract = 1
        return (datetime.now()-timedelta(days=days_to_subtract)).strftime('%Y-%m-%d')

    async def parse_data(self):
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://histock.tw/stock/rank.aspx?p=all", headers = self.HEADER) as res:
                self.data = dict(re.findall("\/stock\/([\d]*?)\'[\s\S]*?\">([\d\.]*?)<\/span>", await res.text()))
    
    async def crawl_data_to_db(self):
        time = self.get_last_data_date()
        with open("top_150_ticker.pkl", "rb") as f:
            tickers = pickle.load(f)
            for ticker in tickers.values():
                # get data from sql
                self.cursor.execute(f"SELECT price FROM stockSuggestor_stock WHERE ticker =?", [ticker])
                rows = self.cursor.fetchall()
                price_time_ls = json.loads(rows[0][0])
                if price_time_ls[-1]["time"] == time:
                    print(f"Alert: <{__name__}> Data already crawled! Terminating crawler")
                    return
                # remove first entry
                price_time_ls.pop(0)
                # add new entry and update
                price_time_ls.append({'time': time, 'value': float(self.data[ticker])}) 
                self.cursor.execute("UPDATE stockSuggestor_stock SET price = ? WHERE ticker = ?",[json.dumps(price_time_ls),str(ticker)])
            self.connect.commit()
    
    async def start(self):
        await self.parse_data()
        await self.crawl_data_to_db()
    async def stream_data(self, ticker, data):
        pass
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(closing_price_crawler("db.sqlite3").start())