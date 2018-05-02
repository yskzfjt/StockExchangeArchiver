import requests
from datetime import datetime, timedelta
import numpy as np

class Stock:
    InvalidValue = -1
    def __init__(self, label, prices):
        self.label = label
        self.prices = []
        self.changes = []
        self.combos = []
        self.valid = False
        self.code = int( label.split( " -- " )[1] )

        #prices
        try:
            for i, p in prices.iteritems():
                p = self.get_valid_value( float(p), prices, i )
                self.prices.append( p )
        except:
            #self.valid == Falseのまま終了
            print( "Wrong Prices Found in " + self.label)
            return

        #changes
        for i in range( len(self.prices) - 1):
            change = self.prices[i+1] - self.prices[i]
            self.changes.append( float(change) )

        #Google URLでは最後の時間が取ってこれないっぽい。
        #最後は変化しなかったことにして数をあわせる
        self.changes.append( float(0) )
        

        #combos
        chain = 0
        for i in range( len(self.changes) ):
            if self.changes[i] > 0:
                chain += 1
            else:
                chain = 0
            self.combos.append( float(chain) )

        #validation
        self.valid = True
        
            
    def get_valid_value( self, price, prices, start ):
        if price == Stock.InvalidValue:
            ofst = -1 if start == len(prices)-1 else 1
            price = next( p for p in prices[ start : : ofst ] if p != Stock.InvalidValue )

        return price

    def _plot( self, xs ):
        x = np.arange( len(xs) )
        y = np.array( xs )
        return x, y
    
    def plot_price_xy( self ):
        return self._plot( self.prices )
    
    def plot_change_xy(self):
        s = 0
        lst = []
        for c in self.changes:
            s += c
            lst.append( s )
        return self._plot( lst )
    
    def plot_combo_xy(self):
        return self._plot( self.combos )
    
