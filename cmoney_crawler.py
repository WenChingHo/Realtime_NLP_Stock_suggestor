from datetime import datetime, timedelta
import time
import bs4
import re
import json
import pandas as pd
import sqlite3
from ABC_Crawler import Crawler
import asyncio
import aiohttp
import pickle 
from my_websocket import RT_updater
from modelpre import getlabel
import random

class cmoney_crawler_rt(Crawler):
    def __init__(self):
        self.connect_to_db()
        
    def connect_to_db(self) -> None:
        super().connect_to_db()

    async def crawl_data_to_db(self):
        size=20
        async with aiohttp.ClientSession() as session:
            tasks = []
            with open("top150_ci.pkl", "rb") as f:
                ticker_ci = pickle.load(f)
                for stock_ticker, ci in ticker_ci.items():
                    df= pd.DataFrame(columns= ["date","time","ticker","username","content","label"])
                    url='https://www.cmoney.tw/follow/channel/getdata/articlelistofstockv2?articleCategory=Personal&channelId=%s&size=%s&sTime=&articleSortType=latest&articleSortCount=0&isIncludeLimitedAskArticle=false&_' % (ci,size)#前500個
                    tasks.append(asyncio.create_task(self.run(session, url, size, df, stock_ticker)))
                await asyncio.wait(tasks)

    async def run(self,session, url, size, df, stock_ticker):
        socket_payload = []
        async with session.get(url) as res:
            try:
                content_json= await res.text()
            except Exception as err:
                print(err, stock_ticker, url, "line39")
                return
            try:
                data=json.loads(content_json)
            except Exception as error:
                print(error, "line 47")
                return
            data.reverse()
            for i in range(size):
                
                df= pd.DataFrame(columns= ["date","time","ticker","username","content","label"])
                cmoney_content_time=data[i]['ArtCteTm'].replace("/","-")
                username = data[i]['ChlCap']
                article_date=datetime.strptime(cmoney_content_time,'%Y-%m-%d %H:%M')
                last_checked=(datetime.now()-timedelta(minutes=1))
                date, time = str(article_date).split()
                if article_date>last_checked:
                    cmoney_content=data[i]['ArtCtn']
                    txt_soup=bs4.BeautifulSoup(cmoney_content,'lxml')
                    content=txt_soup.find('div','main-content').text #發文內容
                    content = content if len(content)<500 else content[:500]
                    label = getlabel(str(content))

                    payload = [date, time, stock_ticker,username, str(content).strip(),label]
                    
                    socket_payload.append(payload)
                    df.loc[len(df)] = payload
                    df.to_sql("stockSuggestor_comments",  self.engine, method='multi',if_exists= "append", index = None)
                    await asyncio.sleep(random.randint(5,7))
                    self.stream_data([payload])
                 
                else:
                    continue

        if len(df)> 0:     
            print(f"\n*******<{__name__}> new comment found for ticker: {stock_ticker}\n",  df)
        else:  print(f"\n*******<{__name__}> No new comment found for ticker: {stock_ticker}\n",  df)
    def stream_data(self, socket_payloads):
        for socket_payload in socket_payloads:
            payload = {'message': socket_payload[4], 
                'category': "chatmsg",
                "name": socket_payload[3],  
                "time":socket_payload[1],  
                "label":socket_payload[5]
                } 
            print(payload)
            messenger = RT_updater(socket_payload[2], json.dumps(payload))
            messenger.run()
            messenger.close()


    async def start(self):
        while True:
            await self.crawl_data_to_db()
            await asyncio.sleep(60)
            

if __name__ == '__main__':
    loop1 = asyncio.get_event_loop()
    loop1.run_until_complete(cmoney_crawler_rt().start())
