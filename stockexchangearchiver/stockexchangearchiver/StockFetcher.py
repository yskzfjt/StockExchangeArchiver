from pytz import timezone
import requests
from datetime import datetime, timedelta
#import matplotlib.pyplot as plt
import numpy as np
import logging

class StockFetcher:
    url = "https://www.google.com/finance/getprices"
    interval = 60 * 5 #sec
    market = "TYO"
    period = "1d"
    column = "d,c"
    market_duration_minute = 360 #min 休憩を含む
    
    #time_zone_offset = 60 * 540 #sec     本番環境だとtime_zone_offsetを入れないとずれてる。
    time_zone_offset = 60 * 0 #sec    ローカルだとtime_zone_offsetを入れるとずれる。

    def __init__(self, code, label, name):
        self.code = code
        self.label = label
        self.name = name
        self.prices = []
        self.timestamps = []

    def fetch_prices(self, timestamps):
        params = {
            'q': self.code,
            'i': StockFetcher.interval,
            'x': StockFetcher.market,
            'p': StockFetcher.period,
            'f': StockFetcher.column
        }

        #googleのはデータ取得開始日を指定できず、
        #最新データからさかのぼって何日分を取ってくるかという指定しかできない。
        #timestampsを見て何日分取ってくるかを調べる。注）timestampsはUTCで来ている
        today = datetime.now()
        if  self.is_aware( timestamps[0] ):
            today = timezone('UTC').localize( today )
        diff = today - timestamps[0]

        #昨日以前の要求なのでその分、データ取得期間を伸ばす.
        if diff.days > 0 :
            params[ 'p' ] = "{}d".format( diff.days + 1 )

        #http リクエスト
        r = requests.get(StockFetcher.url, params=params)

        #http レスポンスを行単位に切る
        lines = r.text.splitlines()
        columns = lines[4].split("=")[1].split(",")

        #ここからが株価
        prices = lines[8:]
        
        base_time = 0
        dct = {}
        for i in range( len(prices) ):
            cols = prices[ i ].split(",")
            if 'a' in cols[0]:
                base_time = int( cols[0].lstrip('a') )
                ofst = 0
            else:
                ofst = int( cols[0] )

            #Unix時間からタイムスタンプを取得。
            d = datetime.fromtimestamp( base_time + ofst * StockFetcher.interval + StockFetcher.time_zone_offset )
            #timestampsはUTCで来ているのでそれに合わせる。
            if  self.is_aware( timestamps[0] ):
                d = timezone('UTC').localize(d)
    
            if  self.just_begining_time(d) or self.just_end_time(d):
                #開始時間ピッタリのやつはおかしいので除外。
                #終了時間ピッタリのやつはないのもあるので除外。
                pass
            else:
                dct[ d ] = float(cols[1])

        #timestampsで要求されているデータに限り登録。
        self.prices = []
        self.timestamps = []
        for t in timestamps:
            self.timestamps.append( t )
            if t in dct:
                self.prices.append( dct[ t ] )
            else:
                self.prices.append( float(-1) )
                
        return self.prices, self.timestamps
    
    def plot_xy( self ):
        x = np.arange( len(self.prices) )
        y = np.array( self.prices )
        return x, y
    
    def within_a_day( self, ofst ):
        return (ofst * StockFetcher.interval) < (StockFetcher.market_duration_minute * 60)
        
    def just_begining_time( self, d ):
        return (d.hour == 9 and d.minute == 0) or (d.hour == 12 and d.minute == 30 )
    
    def just_end_time( self, d ):
        return (d.hour == 15 and d.minute == 0 )

    def is_aware( self, d ):
        return d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None

def get_stock( no ):
    s = StockFetcher( no, "", "" )
    s.fetch_prices()
    return s

def print_stock():
    s0 = get_stock( 6758 )
    s1 = get_stock( 6762 )
    s2 = get_stock( 4503 )
    print( "{}:{} {}:{} {}:{}".format( len(s0.prices), len(s0.timestamps), len(s1.prices), len(s1.timestamps), len(s2.prices), len(s2.timestamps)))
    for i in range( len( s1.prices )):
        
        print( "-----" + str(i) + "----" )
        print( "{}  |  {}  |  {}".format( s0.timestamps[i], s1.timestamps[i], s2.timestamps[i]))
        print( "{}  |  {}  |  {}".format( s0.prices[i], s1.prices[i], s2.prices[i]))

if __name__ == '__main__':
    print_stock()
    pass
    
