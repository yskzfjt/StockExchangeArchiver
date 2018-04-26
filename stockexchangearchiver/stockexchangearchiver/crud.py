# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from stockexchangearchiver import get_model, tasks
from flask import Blueprint, redirect, render_template, request, url_for
from datetime import datetime
from google.cloud import datastore
import pandas as pd
import logging
from . import StockFetcher, Nikkei225

'''
Blueprintはアプリが大きくなったときに、
リクエスト単位でスクリプトファイルを分割したいときに使う。
crud = Blueprint('crud', __name__)

デコレータが@appになってないことに注目
@crud.route("/")
def root():


同じ階層にある別ファイルからはこんなふうにしてアプリに接続
from . import crud
    app.register_blueprint(crud.crud, url_prefix='/archive')
'''
crud = Blueprint('crud', __name__)

#########################################################
##welcome page
#########################################################
@crud.route("/")
def root():
    return "Go  http://stockexchangearchiver.appspot.com/archive/display/ YYYY.MM.DD to view archives ", 200

#########################################################
## google financeからデータ取得。cronで呼ばれるURL
#########################################################
@crud.route('/daily_fetch', methods=['GET'])
def daily_fetch():

    #ここでパブリッシュ
    q = tasks.get_daily_fetch_queue()
    q.enqueue(tasks.process_daily_fetch)
    
    return " Task was published " , 200


#########################################################
## 日付がdateのNikkei225を探して、そのpandasを用意する。
#########################################################
def get_pd( date ):

    #日付でNikkei225を検索
    ds = datastore.Client()
    query = ds.query(kind='Nikkei225')
    query.add_filter('timestamp', '=',  datetime.strptime(date, '%Y.%m.%d'))

    for nk225 in list(query.fetch()):
        #株価のリスト 行インデックス
        stocks = nk225['stocks']
        
        #タイムスタンプのリスト 列インデックス
        timestamps = []

        #タイムスタンプをインデックス用に文字列化
        for i, t in enumerate( nk225['timestamps'] ):
            timestamps.append( t.strftime('%H:%M:%S') )

        #データフレーム作成
        pd_data = pd.DataFrame()
        for i in range( len(stocks) ):
            #株価コード抽出
            code = stocks[ i ].split(" -- ")[1]
            if code not in nk225:
                print( "{} does not exist.".format( stocks[ i ] ) )
            else:
                pd_data[ stocks[ i ] ] = pd.Series( nk225[ code ], index=timestamps )

        #こっちのほうが見やすい
        pd_data.transpose()
        return pd_data

    return None

#########################################################
## URL最後のYYYY.MM.DDに対応するNikkei225をHTMLの表にする。
#########################################################
@crud.route('/display/<date>')
def display(date):
    pd_data = get_pd( date )
    if pd_data is not None:
        return render_template("base.html", date = date, pd_data=pd_data.to_html())
    else:
        return "ERROR:" + date + " does not exist in database.", 200
        
#########################################################
## URL最後のYYYY.MM.DDに対応するNikkei225をCSVにする。
#########################################################
@crud.route('/csv/<date>')
def csv(date):
    pd_data = get_pd( date )
    if pd_data is not None:
        return pd_data.to_csv().replace( "\n", "<br>" )
    else:
        return "ERROR:" + date + " does not exist in database.", 200
        


#########################################################
## 日付がdateのNikkei225を探してリストにして返す
#########################################################
def get_Nikkei225_list( date ):
    ds = datastore.Client()
    query = ds.query(kind='Nikkei225')
    query.add_filter('timestamp', '=',  datetime.strptime(date, '%Y.%m.%d'))
    return list(query.fetch())
    
#########################################################
## デバッグ daily_fetchに失敗しているデータはローカルでこれを呼ぶ
#########################################################
@crud.route('/daily_fetch_old_sync/<date>', methods=['GET'])
def daily_fetch_old_sync( date ):
    for nk225 in get_Nikkei225_list( date ):

        ds = datastore.Client()
        key = ds.key('Nikkei225', int(nk225.id) )

        #株価部分だけ上書き
        for stock in nk225[ "stocks" ]:
            code = int( stock.split( " -- " )[1] )
            s = StockFetcher.StockFetcher( code, "",  ""  )
            s.fetch_prices(  nk225['timestamps'] )
            nk225[ str(code) ] = s.prices

        #データ登録
        entity = datastore.Entity(key=ds.key('Nikkei225'))
        entity.update( nk225 )
        ds.put(entity)

        #古いのは消す
        ds.delete(key)

        #一つしか無いはず
        break

    return " OK " , 200

#########################################################
## デバッグ　ローカルから本日の株価取得
#########################################################
@crud.route('/daily_fetch_sync', methods=['GET'])
def daily_fetch_sync():

    nk = Nikkei225.Nikkei225()
    nk.fetch()
    ds = datastore.Client()

    #古いのは消す
    query = ds.query(kind='Nikkei225')
    query.add_filter('timestamp', '=', nk.get_timestamp())
    try:
        for q in list(query.fetch()):
            logging.info('DELETE')
            key = ds.key('Nikkei225', int(q.id) )
            ds.delete(key)
    except:
        logging.info('DELETE EXCEPTION')

    #fetch_all
    for i in range( len(nk.stocks) ):
        s = nk.stocks[ i ]
        s.fetch_prices( nk.timestamps )

    #データ作成
    dct = {
        'timestamp': nk.get_timestamp(),
        'stocks':[ s.label+" -- "+str(s.code) for s in nk.stocks ],
        'timestamps': nk.timestamps
    }
    for s in nk.stocks:
        dct[ s.code ] = s.prices

    #データ登録
    entity = datastore.Entity(key=ds.key('Nikkei225'))
    entity.update( dct )
        
    ds.put(entity)
    logging.info('PUT')

    return " OK " , 200


'''
@crud.route('/add', methods=['GET', 'POST'])
def add():
    return "dummy", 200

# [START list]
@crud.route("/")
def list2():
    token = request.args.get('page_token', None)
    if token:
        token = token.encode('utf-8')

    books, next_page_token = get_model().list2(cursor=token)

    return render_template(
        "list.html",
        books=books,
        next_page_token=next_page_token)
# [END list]


@crud.route('/<id>')
def view(id):
    book = get_model().read(id)
    return render_template("view.html", book=book)

# [START add]
@crud.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        book = get_model().create(data)

        return redirect(url_for('.view', id=book['id']))


    return render_template("form.html", action="Add", book={})
# [END add]


@crud.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    book = get_model().read(id)

    if request.method == 'POST':
        data = request.form.to_dict(flat=True)

        book = get_model().update(data, id)

        return redirect(url_for('.view', id=book['id']))

    return render_template("form.html", action="Edit", book=book)


@crud.route('/<id>/delete')
def delete(id):
    get_model().delete(id)
    return redirect(url_for('.list'))
'''
