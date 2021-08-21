import sqlite3 as sql
import pandas as pd 
import matplotlib
matplotlib.use('Agg')       # 在後端執行不顯示圖片的方法
import matplotlib.pyplot as plt
import mplfinance as mpf
import talib
import os
import shutil
import pickle

dbfile = "StockData.db"
conn = sql.connect(dbfile)

def pick_top_150():
    file_path = './image'
    shutil.rmtree(file_path)   #重建資料夾 避免上一天的圖檔殘留
    os.mkdir(file_path)
    with open("top_150_ticker.pkl", "rb") as f:
        data = pickle.load(f)
    id_list = list(data.values())
    # print(id_list)
    for stockid in id_list:
        df = pd.read_sql("SELECT date,開盤價,最高價,最低價,收盤價,成交股數 FROM stock_price where stock_id = '{}' order by date DESC limit 300".format(stockid), conn).iloc[::-1]
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        df.index = df['Date']
        df.index = pd.DatetimeIndex(df.index)
        df = df.drop(columns=['Date'])
        df['k'], df['d'] = talib.STOCH(df['High'],
                                df['Low'],
                                df['Close'],
                                fastk_period=9,
                                slowk_period=3,
                                slowk_matype=1,
                                slowd_period=3,
                                slowd_matype=1)
        df['upper'], df['middle'], df['lower']= talib.BBANDS(df['Close'],
                                                      timeperiod=20,
                                                      nbdevdn=2.1,
                                                      matype=0)

        mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
        s  = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)
        add_plot = [mpf.make_addplot(df[['upper', 'lower']], linestyle='dashdot'),
                        mpf.make_addplot(df['middle'], linestyle='dotted', color='y'),
                        mpf.make_addplot(df['k'], panel=2, color='b'),
                        mpf.make_addplot(df['d'], panel=2, color='r')]
        kwargs = dict(type='candle', volume = True, figscale=0.8, style=s, addplot=add_plot)  #figsize(20, 10) => 大圖
        mpf.plot(df, **kwargs)
        plt.savefig('./image/{}.jpg'.format(stockid), bbox_inches="tight")


        


pick_top_150()