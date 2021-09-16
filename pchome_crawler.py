
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

class pchome_crawler_rt(Crawler):
    def __init__(self, min:0, sec:30):
        self.connect_to_db()
        self.min = min
        self.sec = sec
    def connect_to_db(self) -> None:
        super().connect_to_db()
   
    async def find_links(self, ticker:str)->None:
        async with aiohttp.ClientSession() as s:
            async with s.post(f'https://pchome.megatime.com.tw/stock/sto5/sid{ticker}.html', headers = self.HEADER, data = {'is_check':'1'}) as res:
                html_text = await res.text()
                print(ticker)
                url_pattern = f'/news/cat1/({datetime.now().strftime("%Y%m%d")}.*)\"  class=\"news18\">(.*?)<[\s\S]*?icDate\">\((.*?)\)'
                url_titles = re.findall(url_pattern, html_text)

                if url_titles:
                    return await self.crawl_data_to_db(ticker, url_titles, s)
                return (ticker, 0)

    def stream_data(self, ticker, data):
        payload = {'title': data[1], #爬到的留言
            'category': "news",
            "publisher": data[0],  #爬蟲的名字
            "time":data[2],  #爬到的時間
            "url":data[3]
            } 
        messenger = RT_updater(ticker, json.dumps(payload))
        messenger.run()
        messenger.close()

    async def crawl_data_to_db(self, ticker:str, url_title:list, session:object)->None:
        df= pd.DataFrame(columns= ["date","time","publisher", "ticker","url","title","content"])
        print(url_title)
        new_comment_count = 0
        #restict search zone to time since last crawled + 1 minute buffer time
        time_since_last_crawled = datetime.now()-timedelta(minutes= self.min)
        #Reverse the list so the most recent data is shown at the top
        url_title.reverse() 

        for url, title, date in url_title:
            news_publish_time = datetime.strptime(date[:11],'%m-%d %H:%M').replace(year=datetime.today().year)
            # 避免重複存取新聞
            print(news_publish_time)
            if news_publish_time < time_since_last_crawled : 
                print(news_publish_time)
                continue

            print("_"*50 + f"Pchome {ticker}:" + "_"*50 + "\nurl: " + url + '\nTitle: ' + title)

            # handle post request informality on their website
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
                accurate_title_time = re.findall(f"\">({title[:-4]}.*?)<\/a>[\s\S]*?\((.*?)\)", html_text)
                print(accurate_title_time)
                print(type(accurate_title_time))
                strict_article_time = datetime.strptime(accurate_title_time[0][1], '%Y-%m-%d %H:%M:%S')

                print(strict_article_time, time_since_last_crawled)
                if strict_article_time < time_since_last_crawled: continue

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

                df= pd.DataFrame(columns= ["date","time","publisher", "ticker","url","title","content","label"])
                payload = [accurate_title_time[0][1][:10], accurate_title_time[0][11:], data[2], ticker, f'https://pchome.megatime.com.tw/news/cat1/{url}' , accurate_title_time[0][0], trimmed_content]
                self.stream_data(ticker, [data[2],title,data[1],f'https://pchome.megatime.com.tw/news/cat1/{url}'])
                print(payload)
                df.loc[len(df)] = payload
        if not df.empty:
            df.to_sql("stockSuggestor_news", self.engine, if_exists='append', index=False, chunksize=10000)  
            pass
        return (ticker, new_comment_count)

    async def start(self):
        if self.min: self.time_between_search = self.min*60 +self.sec
        with open("top_150_ticker.pkl", "rb") as f:
            ticker_dict = pickle.load(f)
            tasks = []
            while True:
                for ticker in ticker_dict.values():
                    try:
                        tasks.append(asyncio.create_task(self.find_links(ticker)))
                    except Exception as err:
                        print(err)
                await asyncio.wait(tasks) 
                #print(last_title)       
                await asyncio.sleep(self.time_between_search)
                
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pchome_crawler_rt(min =1, sec = 0).start())
