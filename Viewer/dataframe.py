import sys
try:
    del sys.modules['stock']
except Exception as e:
    pass

import requests
from datetime import datetime, timedelta
import pandas as pd
import sys
from io import StringIO

import pandas as pd

from stock import Stock

class DataFrame:
    '''
    YY.MM.DDの引数でCSVを引っ張ってくる
    '''
    url = "http://stockexchangearchiver.appspot.com/archive/csv/"
    def __init__(self ):
        self.timestamp_string = ""
        self.csv = ""
        self.data = None
        self.corr = None
        self.stocks = []
        self.combo_info_list = []
        

    def get_corr( self ):
        if self.data is None:
            self.corr = None
        elif self.corr is None:
            self.corr = self.data.corr()

        return self.corr

    def get_timestamps( self ):
        return self.data[ self.data.columns[0] ]

    def find_timestamps( self, tgt ):
        for i,ts in enumerate(self.get_timestamps()):
            if ts == tgt: return i
        return -1

    def get_combo_info_list( self, combo_count ):
        tss = self.get_timestamps()
        for i,ts in enumerate( self.get_timestamps() ):
            lst = []
            for s in self.stocks:
                if combo_count <= s.combos[ i ] and s.changes[ i ] > 0 :
                    lst.append( s )
            if len(lst ) > 2:
                self.combo_info_list.append( {"timestamp":ts, "stocks":lst} )

        return self.combo_info_list

    def display( self ):
        pd.set_option('display.max_columns', 225)
        pd.set_option('display.max_rows', 100)
        display( self.data )
        
    def fetch( self, ts ):
        self.timestamp_string = ts
        r = requests.get(DataFrame.url + self.timestamp_string)
        self.csv = r.text.replace("<br>", "\n")
        pd.set_option('display.max_columns', 225)
        pd.set_option('display.max_rows', 100)
        self.data = pd.read_csv( StringIO( self.csv ), delimiter=',' )
        self.corr = None

        #最初のコラムはラベルなので除外
        for no, lbl in enumerate(self.data.columns):
            if no != 0:
                self.stocks.append( Stock( lbl, self.data[ lbl ] ) )
        
        return self.data

