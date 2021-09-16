
import re
from datetime import datetime, timedelta
import time
import sqlite3
import pandas as pd
import pickle
from ABC_Crawler import Crawler
import asyncio
import aiohttp
import json
from my_websocket import RT_updater
from sqlalchemy import create_engine

class pchome_crawler(Crawler):
    def __init__(self):
        self.connect_to_db()
        
    def connect_to_db(self):
        super().connect_to_db()
   
    async def find_links(self, ticker:str)->None:
        async with aiohttp.ClientSession() as s:
            async with s.post(f'https://pchome.megatime.com.tw/stock/sto5/sid{ticker}.html', headers = self.HEADER, data = {'is_check':'1'}) as res:
                # find title and url
                html_text = await res.text()
                url_pattern = f'\/news\/cat1\/({(datetime.today()).year}.*)\"  class=\"news18\">(.*?)<span class=\"ic[\s\S]*?>\((.*?)\)<\/span>'
                url_titles = re.findall(url_pattern, html_text)
                if url_titles:
                    print("_"*50+'\n', f"<{__name__}> {ticker}: \n", url_titles)
                    return await self.crawl_data_to_db(ticker, url_titles, s)
                return (ticker, 0)

    def stream_data(self, ticker, publisher, date, time, title, url ):
        payload = {'title': title,
            'category': "news",
            "publisher": publisher,  #news publisher
            "date": date,
            "time":time,  #YYYY-MM-DD HH:MM:SS
            "url":url
            } 
        messenger = RT_updater(ticker, json.dumps(payload))
        messenger.run()
        messenger.close()

    async def crawl_data_to_db(self, ticker, url_title:list, session:object):
        df= pd.DataFrame(columns= ["date","time","publisher", "ticker","url","title","content","label"])

        new_comment_count = 0
        url_title.reverse()
        timeframe = (datetime.now()-timedelta(days=1)).replace(hour=14)
        for url, title, date in url_title:
            news_publish_time = datetime.strptime(date[:11],'%m-%d %H:%M').replace(year=datetime.today().year)
            print(news_publish_time)
            if news_publish_time < timeframe: continue
            html_text = ""
            print("_"*50 + f"Pchome {ticker}:" + "_"*50 + "\nurl: " + url + '\nTitle: ' + title)
            try:
                async with session.post(
                    f'https://pchome.megatime.com.tw/news/cat1/{url}',
                    data = {'is_check':'1'},
                    headers = self.HEADER
                    ) as res:

                    html_text = await res.text()
            except:
                async with session.post(
                    f'https://pchome.megatime.com.tw/news/cat1/{url}',
                    data = {'is_check':'1 '},
                    headers = self.HEADER
                    ) as res:
                    html_text = await res.text()

            accurate_title_time = re.findall(f"\">({title[:-4]}.*?)<\/a>[\s\S]*?\((.*?)\)", html_text)
            article_datetime = datetime.strptime(accurate_title_time[0][1], '%Y-%m-%d %H:%M:%S')
            article_time = accurate_title_time[0][1]
            article_title = accurate_title_time[0][0]
            if article_datetime< timeframe: continue
            regex = f"即時新聞內文 開始[\s\S]*?({title[:-4]}[\s\S]*?)<\/div>|newsarticle start([\s\S]*)?<\/article>"
            content = max(re.findall(regex, html_text), key = len) #returns a list of tuples

            if len(content)>1:
                trimmed_content = max([re.sub("[^，。\u4e00-\u9fa51-9]","",i) for i in content],key=len)  
            else:
                trimmed_content = re.sub("[^，。\u4e00-\u9fa51-9]","", max(content, key=len))

            new_comment_count +=1
            # data to add to df
            article_publisher = date.split()[2]
            payload = [
                article_time[:10],
                article_time[11:], 
                article_publisher,
                ticker, 
                f'https://pchome.megatime.com.tw/news/cat1/{url}', 
                article_title, 
                trimmed_content if len(trimmed_content)<1000 else trimmed_content[:1000], 
                "T"
            ]
            #df columns: (ticker, publisher, date, time, title, url ):
            self.stream_data(
                ticker, 
                article_publisher, 
                article_time[:10],
                article_time[11:],
                article_title,
                f'https://pchome.megatime.com.tw/news/cat1/{url}'
            )
            df.loc[len(df)] = payload
        if len(df):
            try:
                df.to_sql("stockSuggestor_news", self.engine, if_exists='append', index=False, chunksize=10000) 
            except Exception as err:
                print(err)  
            return (ticker, new_comment_count)

    async def start(self):
        with open("top_150_ticker.pkl", "rb") as f:
            ticker_dict = pickle.load(f)
            tasks = []
            while True:
                for ticker in ticker_dict.values():#ticker_dict.values():
                    tasks.append(asyncio.create_task(self.find_links(ticker)))
                await asyncio.wait(tasks) 
                await asyncio.sleep(500)

                
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pchome_crawler().start())
