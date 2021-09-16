from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from django.conf import settings



class Crawler(ABC):
    
    HEADER = {
        "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
        'Connection':'open',
    }

    def __init__(self):
        pass

    @abstractmethod
    def connect_to_db(self):
        self.db_connection_url = "postgresql://eddie@localhost:5432/stocksuggestordb"
        self.engine = create_engine(self.db_connection_url)
        #df.to_sql("stockSuggestor_streamdata", engine, if_exists='replace', index=False, chunksize=10000)  
        
    @abstractmethod
    async def crawl_data_to_db(self):
        pass

    @abstractmethod
    def stream_data(self, ticker, data):
        pass
    
    @abstractmethod
    def start(self):
        pass
    



