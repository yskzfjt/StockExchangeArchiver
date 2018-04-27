import requests
from datetime import datetime, timedelta
import pandas as pd
import sys
from io import StringIO

import pandas as pd


class DataFrame:
    url = "http://stockexchangearchiver.appspot.com/archive/csv/"
    def __init__(self ):
        self.timestamp_string = ""
        self.csv = ""
        self.data = None

    def timestamp2string( self, ts ):
        return ts.strftime('%H:%M:%S')

    def fetch( self, ts ):
        self.timestamp_string = ts
        r = requests.get(DataFrame.url + self.timestamp_string)
        self.csv = r.text.replace("<br>", "\n")
        pd.set_option('display.max_columns', 225)
        pd.set_option('display.max_rows', 100)
        self.data = pd.read_csv( StringIO( self.csv ), delimiter=',' )
        return self.data

