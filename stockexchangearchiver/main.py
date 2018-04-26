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

import stockexchangearchiver
import config

app = stockexchangearchiver.create_app(config)

#GAEはURLレスポンスタイムに一分の時間制限がある。
#daily_fetchがその制限に引っかかってしまうのでPUB/SUBを使う。
#PUB/SUBのキューは外部のpsqworkerというプログラムから見える必要があるので、
#app_context()はget_daily_fetch_queue内部でカレントアプリの値を参照できるようにする。
with app.app_context():
    daily_fetch_queue = stockexchangearchiver.tasks.get_daily_fetch_queue()

# This is only used when running locally. When running live, gunicorn runs
# the application.
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
