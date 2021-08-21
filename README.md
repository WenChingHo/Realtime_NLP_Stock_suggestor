# Real-time Stock Suggestor 

## Table of contents
* [Intro / General info](#general-info)
* [Technologies](#technologies)


## General info: 
#### Statement of Purpose:</b><br>
This final project was made with the goal to creating a platform that crawls and combines all the essential information that are scattered all over the internet, and present it with a clean and interactive web application to help users make better and more informed decision on day trading (What constitute as "essential information" is based on <b>my<b> preference)
<br>
#### Components: <br>
1. Web crawlers (asyncio & Scrapy) that scrapes major news outlets and comment thread <br>
2. NLP model (CNN + LSTM) that process the crawled data from (step 1) and determine public opinion on the stock market <br>
3. Price predictor model (GRU && LSTM) that use previous market data to make a guesstimate on today's market trend <br>
4. Django + channels (Redis) + WebSockets to create a real-time chatbox that combines multiple comment threads throughout the internet, allowing users to see what other people on different platforms are talking about!<br>
5. Shioaji API to get streaming stock data
 <br><br>
<img src="https://github.com/WenChingHo/Realtime_NLP_Stock_suggestor/blob/main/server%20bp.png" width="800"> | <img 


## Technologies:
#### Web application:
- Django
- Redis (on Docker)
- reconnecting-websocket
- HTML/CSS/Javascript/JQuery/Bootstrap
                                                                                                                    
#### Model training:                                                                                        
- Python 3.8
- Tensorflow 2.5.0
- Scikit-learn
- Shiaoji

#### Crawlers:    
- ABC.meta
- Asyncio
- Aiohttp
- Pyppeteer
- Scrapy
- Bs4
- Regex                                                                                                         


