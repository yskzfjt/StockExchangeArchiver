from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
import re
from . import StockFetcher
from datetime import datetime
from datetime import timedelta
from google.cloud import datastore

class Nikkei225:
    # アクセスするURL
    url = "https://indexes.nikkei.co.jp/nkave/index/component?idx=nk225"

    interval = 5 * 60 #sec
    am_start = 9
    am_duration = 2.5 * 60 * 60 #sec
    pm_start = 12.5
    pm_duration = 2.5 * 60 * 60 #sec
    
    def __init__( self ):
        self.title = ""
        self.date = ""
        self.stocks = []
        self.timestamps = []


    #最終更新日時からdatetimeを取得
    def get_timestamp( self ):
        return datetime.strptime(self.date, '%Y.%m.%d')

    #最終更新日時を取得
    def fetch_date( self, soup ):
        divs = soup.find_all("div", class_="last-update" )
        assert len(divs)==1, "no last-update class found."
        self.date = divs[0].string
        self.date = self.date.split('：')[1]
        self.make_timestamps()

    #開始時間のdatetimeを取得
    def get_start_timestamp( self, time ):
        ts = self.get_timestamp()
        return datetime( ts.year, ts.month, ts.day ) + timedelta(hours=time)

    #取得するデータのタイムスタンプを作成。
    def make_timestamps( self ):
        tick = timedelta( seconds=Nikkei225.interval )
        starts = [ Nikkei225.am_start, Nikkei225.pm_start ]
        durations = [ Nikkei225.am_duration, Nikkei225.pm_duration ]
        for start, duration in zip(starts, durations):
            bgn = self.get_start_timestamp( start )
            end = bgn + timedelta( seconds=duration )
            while bgn < end:
                bgn += tick
                self.timestamps.append(  bgn )

    #取得するデータの銘柄を取得
    def fetch_stock( self, soup ):
        divs = soup.find_all("div", class_=re.compile("row component-list.*") )
        
        for tag in divs:
            # classの設定がされていない要素は、tag.get("class").pop(0)を行うことのできないでエラーとなるため、tryでエラーを回避する
            try:
                code_ = tag.find_all("div", class_="col-xs-3 col-sm-1_5")[0].string
                label_ = tag.find_all("div", class_="col-xs-9 col-sm-2_5")[0].string
                company_ = tag.find_all("div", class_="hidden-xs col-sm-8")[0].string
                s = StockFetcher.StockFetcher(code_, label_, company_)
                self.stocks.append( s )
            except:
                # パス→何も処理を行わない
                pass
        
    #日経のURLからHTMLを取得して、日付、タイムスタンプ、銘柄をスクレイピング
    def fetch( self ):
        html = urllib.request.urlopen(self.url)
        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.title
        self.title = title_tag.string

        self.fetch_date( soup )
        self.fetch_stock( soup )

def print_stocks():
    n = Nikkei225()
    n.fetch()
    for i,t in enumerate(n.timestamps):
        print( "{:2}  {}".format( i, t ) )
    
    '''
    print( n.title )
    print( n.date )
    for i, s in enumerate( n.stocks ):
        print( "{:3}: {}".format( i, s ) )
    '''
    
if __name__ == '__main__':
    #print_stocks()
    pass
    
                             
                             
