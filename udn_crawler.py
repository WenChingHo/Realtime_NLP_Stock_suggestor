from ABC_Crawler import Crawler
import requests
import re
from datetime import datetime
import time
import pandas as pd
import asyncio
import aiohttp


class udn_crawler(Crawler):
    
    def __init__(self, database):
        self.connect_to_db(database)
        
    def connect_to_db(self,database) -> None:
        super().connect_to_db(database)
    
    def find_top_links(self)->list:
        # find all the links and store the url, title, time, publisher
        url_title_top=[]
        for i in range(1,3):
            req = requests.get(f"https://money.udn.com/rank/pv/1001/5590/{i}", headers = self.HEADER)
            url_pattern = 'href=\"(https:\/\/money.udn.com\/money\/story\/.*?)\">(.*?)<\/a>[\S\s]*?({}.*?)<\/td>[\S\s]*?only_web\">(.*?)<\/td>'.format(datetime.now().strftime("%m"))
            article_info = re.findall(url_pattern, req.text)
            #print(article_info)
            url_title_top.append(article_info)
        return url_title_top

    def find_new_link(self)->list:
        # find all the links and store the url, title, time, publisher
        url_title_new = []
        for i in range(1,3):
            req_new = requests.get(f"https://money.udn.com/rank/newest/1001/5590/{i}", headers = self.HEADER)
            url_pattern_new = 'href=\"(https:\/\/money.udn.com\/money\/story\/.*?)\">(.*?)<\/a>[\S\s]*?only_1280\"\>({}.*?)<\/td>'.format(datetime.now().strftime("%m"))
            article_info_new = re.findall(url_pattern_new, req_new.text)
            #print(article_info_new)
            url_title_new.append(article_info_new)
        return url_title_new

    async def run_top(self, data, session, df, HEADER):
        (url, title, date, view ) = data 
        async with session.get(url, headers = HEADER) as res:
            try:
                raw_text = await res.text()
                content = re.search('\"article_body\">([\s\S]*?)story\_bady', raw_text).group(1)
                news_content = "".join(re.findall("<p>\s*(.*?)。<", content))
                date, hour = date.split()
                df.loc[len(df)] = [datetime.now().strftime("%Y/")+date, hour, view, "Top_stock", url, title, news_content]
            except Exception as err:
                print(err)
    
    async def run_new(self, data, session, df, HEADER):
        (url, title, date) = data 
        async with session.get(url, headers = HEADER) as res:
            try:
                raw_text = await res.text()
                content = re.search('\"article_body\">([\s\S]*?)story\_bady', raw_text).group(1)
                news_content = "".join(re.findall("<p>\s*(.*?)。<", content))
                date, hour = date.split()
                df.loc[len(df)] = [datetime.now().strftime("%Y/")+date, hour, "NA", "new_stock", url, title, news_content]
            except Exception as err:
                print(err)

    async def crawl_data_to_db(self, crawled_title, url_title_top, url_title_new)->None:
        async with aiohttp.ClientSession() as session:  
            df= pd.DataFrame(columns= ["date","hour", "view", "ticker","url","title","content"])
            
            url_title_top = [ item for items in url_title_top for item in items ]
            url_title_new = [ item for items in url_title_new for item in items ]
            
            tasks = []
            try:
                for data in url_title_new:
                    #print("new: ", data)
                    if data[1] in crawled_title: break
                    crawled_title.append(data[1])
                    tasks.append(asyncio.create_task(self.run_new(data, session, df, self.HEADER)))

                for data in url_title_top:
                    #print("top: ", data)
                    if data[1] in crawled_title: break
                    crawled_title.append(data[1])
                    tasks.append(asyncio.create_task(self.run_top(data, session, df, self.HEADER)))
                await asyncio.wait(tasks)
            except: 
                print("************ No new website were found!**************")
        
            print(f"{__name__} added: ", df)
            df.to_sql("udn", self.connect, if_exists="append", index=False)
            self.connect.commit()
        
    async def start(self):
        crawled_title= []
        while True:
            url_title_top = self.find_top_links()
            url_title_new = self.find_new_link()
            await self.crawl_data_to_db(crawled_title, url_title_top, url_title_new)
            await asyncio.sleep(30)
            
if __name__ == '__main__':
    loop1 = asyncio.get_event_loop()
    loop1.run_until_complete(udn_crawler("News.db").start())
