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

import logging

#from bookshelf import get_model, storage
from flask import current_app
from google.cloud import pubsub, datastore
import psq
import requests
from . import Nikkei225, StockFetcher


# [START get_books_queue]
publisher_client = pubsub.PublisherClient()
subscriber_client = pubsub.SubscriberClient()


def get_daily_fetch_queue():
    project = current_app.config['PROJECT_ID']

    # Create a queue specifically for processing books and pass in the
    # Flask application context. This ensures that tasks will have access
    # to any extensions / configuration specified to the app, such as
    # models.
    return psq.Queue(
        publisher_client, subscriber_client, project,
        'daily_fetch_queue', extra_context=current_app.app_context)
# [END get_books_queue]


def process_daily_fetch():
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
    #for i in range( 5 ):
    for i in range( len(nk.stocks) ):
        s = nk.stocks[ i ]
        s.fetch_prices( nk.timestamps )
        logging.info('FETCH ' + str(i))
        
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
    return

'''
# [START process_book]
def process_daily_fetch( date ):
    """
    Handles an individual Bookshelf message by looking it up in the
    model, querying the Google Books API, and updating the book in the model
    with the info found in the Books API.
    """

    model = get_model()

    book = model.read(book_id)

    if not book:
        logging.warn("Could not find book with id {}".format(book_id))
        return

    if 'title' not in book:
        logging.warn("Can't process book id {} without a title."
                     .format(book_id))
        return

    logging.info("Looking up book with title {}".format(book[
                                                        'title']))

    new_book_data = query_books_api(book['title'])

    if not new_book_data:
        return

    book['title'] = new_book_data.get('title')
    book['author'] = ', '.join(new_book_data.get('authors', []))
    book['publishedDate'] = new_book_data.get('publishedDate')
    book['description'] = new_book_data.get('description')

    # If the new book data has thumbnail images and there isn't currently a
    # thumbnail for the book, then copy the image to cloud storage and update
    # the book data.
    if not book.get('imageUrl') and 'imageLinks' in new_book_data:
        new_img_src = new_book_data['imageLinks']['smallThumbnail']
        book['imageUrl'] = download_and_upload_image(
            new_img_src,
            "{}.jpg".format(book['title']))

    model.update(book, book_id)
# [END process_book]


# [START query_books_api]
def query_books_api(title):
    """
    Queries the Google Books API to find detailed information about the book
    with the given title.
    """
    r = requests.get('https://www.googleapis.com/books/v1/volumes', params={
        'q': title
    })

    try:
        data = r.json()['items'][0]['volumeInfo']
        return data

    except KeyError:
        logging.info("No book found for title {}".format(title))
        return None

    except ValueError:
        logging.info("Unexpected response from books API: {}".format(r))
        return None
# [END queue_books_api]


def download_and_upload_image(src, dst_filename):
    """
    Downloads an image file and then uploads it to Google Cloud Storage,
    essentially re-hosting the image in GCS. Returns the public URL of the
    image in GCS
    """
    r = requests.get(src)

    if not r.status_code == 200:
        return

    return storage.upload_file(
        r.content,
        dst_filename,
        r.headers.get('content-type', 'image/jpeg'))
'''
