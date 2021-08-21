
import re
from datetime import datetime
import time
import sqlite3
import pandas as pd
import pickle
from ABC_Crawler import Crawler
import asyncio
import aiohttp
import json

class pchome_crawler(Crawler):
    def __init__(self, database:str):
        self.connect_to_db(database)
        
    def connect_to_db(self, database:str) -> None:
        super().connect_to_db(database)
   
    async def find_links(self, ticker:str, last_title:dict)->None:
        async with aiohttp.ClientSession() as s:
            async with s.post(f'https://pchome.megatime.com.tw/stock/sto5/sid{ticker}.html', headers = self.HEADER, data = {'is_check':'1'}) as res:
                # regex找超連結跟標題
                html_text = await res.text()
                print(ticker)
                url_pattern = f'/news/cat1/({datetime.now().strftime("%Y%m%d")}.*)\"  class=\"news18\">(.*?)<[\s\S]*?icDate\">\((.*?)\)'
                url_titles = re.findall(url_pattern, html_text)
                if url_titles:
                    print("_"*50+'\n', f"<{__name__}> {ticker}: \n", url_titles)
                    return await self.crawl_data_to_db(ticker, url_titles, last_title, s)
                return (ticker, 0)
    
    async def crawl_data_to_db(self, ticker, url_title:list, last_title:dict, session:object):
        df= pd.DataFrame(columns= ["date","time","publisher", "ticker","url","title","content"])
        # get last crawled data
        ltitle = last_title[ticker] if ticker in last_title else ""
        # add newest title as the title
        last_title[ticker]= url_title[0][1]
        new_comment_count = 0
        for url, title, date in url_title:
            print(title, ltitle)
            # 避免重複存取新聞
            if title == ltitle: 
                print("duplicate title")
                break
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
            finally:    
                regex = f"即時新聞內文 開始[\s\S]*?({title[:-4]}[\s\S]*?)<\/div>|newsarticle start([\s\S]*)?<\/article>"
                content = max(re.findall(regex, html_text), key = len) #returns a list of tuple
                # 找到最長的 = 新聞內容
                if len(content)>1:
                    trimmed_content = max([re.sub("[^，。\u4e00-\u9fa51-9]","",i) for i in content],key=len)  
                else:
                    trimmed_content = re.sub("[^，。\u4e00-\u9fa51-9]","", max(content, key=len))
                new_comment_count +=1
                # 要加到df上的資料
                data = date.split()
                payload = [datetime.now().strftime("%Y/%m/%d %H:%M:%S"), data[1], data[2], ticker, f'https://pchome.megatime.com.tw/news/cat1/{url}' , title, trimmed_content]
                print(payload)
                df.loc[len(df)] = payload
        if df.empty:
            df.to_sql(f'pchome', self.connect, if_exists='append', index=False)
            self.connect.commit()
        return (ticker, new_comment_count)

    async def start(self):
        with open("top_150_ticker.pkl", "rb") as f:
            ticker_dict = pickle.load(f)
            tasks = []
            last_title={}
            while True:
                for ticker in ticker_dict.values():
                    try:
                        tasks.append(asyncio.create_task(self.find_links(ticker, last_title)))
                    except Exception as err:
                        print(err)
                await asyncio.wait(tasks) 
                #print(last_title)       
                await asyncio.sleep(30)
                
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pchome_crawler("News.db").start())
