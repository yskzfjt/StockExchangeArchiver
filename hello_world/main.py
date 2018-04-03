# Copyright 2015 Google Inc. All Rights Reserved.
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

# [START app]
import logging

from flask import Flask
import requests
from datetime import datetime, timedelta

url = "https://www.google.com/finance/getprices"
code = 7203
lsat_date = datetime.now() #データの取得開始日
interval = 60  #データの間隔(秒)。1日 = 86400秒
market = "TYO"  #取引所のコード　TYO=東京証券取引所
period =  "2d" #データを取得する期間

params = {
  'q': code,
  'i': interval,
  'x': market,
  'p': period,
  'ts': lsat_date.timestamp()
}


app = Flask(__name__)


@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    r = requests.get(url, params=params)
    return r.text.replace('\n', '<br>')
    #return 'Hello World!'


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END app]
