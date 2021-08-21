from abc import ABC, abstractmethod
import threading
import sqlite3

class Crawler(ABC):
    
    HEADER = {
        "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Connection':'open',
    }
    
    def __init__(self ):
        pass

    def connect_to_db(self, database):
        self.connect = sqlite3.connect(database)
        self.cursor = self.connect.cursor()    
        
    @abstractmethod
    async def crawl_data_to_db(self):
        pass

    @abstractmethod
    def stream_data(self, ticker, data):
        pass
    
    @abstractmethod
    def start(self):
        pass
    



