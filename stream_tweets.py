import requests
import threading
import os
import sys
import json
import tweet_db
import time
from datetime import datetime
from collections import defaultdict
import telegram
from telegram.ext import MessageHandler, Filters
from preprocess_tweet import findall_hashtags


OG_HTS = {"#StopArmenianAggression",
          "#ArmenianMilitaryCoup",
          "#ArmenianGovernmentTrolls",
          "#StopArmenianTerrorism",
          "#babykillerarmenia",
          "#WakeUpArmenia",
          "#ArmeniaKillsChildren",
          "#StopArmenianTerror",
          "#KarabakhisAzerbaijan",
          "#Azerbaijanphobia",
          "#DontBelieveArmenia",
          "#StopArmenianLies"}

NEW_HASHTAGS = defaultdict(int)

CHAT_ID = -575829070

TG_TOKEN = os.environ.get("TELEGRAM_ACCESS_TOKEN")

mutex = threading.Lock()


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def get_rules(headers):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", headers=headers
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(headers, rules):
    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print(json.dumps(response.json()))


def generate_stream_rules():
    return " OR ".join(OG_HTS)


def set_rules(headers):
    # You can adjust the rules if needed
    rules = [
        {"value": f"({generate_stream_rules()}) lang:en"},
    ]
    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=headers,
        json=payload,
    )
    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))


def find_hashtags(object_data_str):
    object_data = json.loads(object_data_str)
    content = object_data.get('data', {}).get('text', '')
    hashtags = findall_hashtags(content)
    for ht in hashtags:
        if ht not in OG_HTS:
            NEW_HASHTAGS[ht] += 1
            if NEW_HASHTAGS[ht] >= 10:
                send_hashtag(ht)


def restart_connection(response, tweetDb):
    print('Closing response....\n')
    response.close()
    tweetDb.conn.commit()
    tweetDb.conn.close()
    time.sleep(60)
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print(f'Sleeping done. Calling main again at {now}.\n')
    start_streaming_tweets()


def get_stream(headers, set_, bearer_token, tweetDb):
    start_time = round(time.time())
    while True:
        try:
            response = requests.get(
                "https://api.twitter.com/2/tweets/search/stream?tweet.fields=source,possibly_sensitive,entities,text,referenced_tweets&expansions=author_id,geo.place_id", headers=headers, stream=True,
            )
            print(response.status_code)

            if response.status_code != 200:
                raise Exception(
                    "Cannot get stream (HTTP {}): {}".format(
                        response.status_code, response.text
                    )
                )
            try:
                for response_line in response.iter_lines():
                    if response_line:
                        json_response = json.loads(response_line)
                        object_data = json.dumps(json_response, indent=4, sort_keys=True)
                        print(object_data)
                        tweetDb.insert(object_data)
                        find_hashtags(object_data)
                        duration = round(time.time()) - start_time
                        if duration > 2*60*60: #generates a new connection every 2 hours to avoid closed connections
                            restart_connection(response, tweetDb)
            except requests.exceptions.ChunkedEncodingError:
                pass
        except KeyboardInterrupt:
            tweetDb.conn.commit()
            tweetDb.conn.close()
            quit()


def start_streaming_tweets():
    print("started thread one")
    bearer_token = os.environ.get("TWITTER_AUTH_BEARER_TOKEN")
    headers = create_headers(bearer_token)
    rules = get_rules(headers)
    delete_all_rules(headers, rules)
    set_ = set_rules(headers)
    tweetDb = tweet_db.TweetDb(db_file=sys.argv[1], should_create_tables=True)
    get_stream(headers, set_, bearer_token, tweetDb)


def send_hashtag(ht):
    bot = telegram.Bot(token=TG_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=ht)


def start_dispatch():
    def add_hashtag(update, context):
        mutex.acquire()
        try:
            OG_HTS.add(update.message.text[1:])
        finally:
            mutex.release()
        context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


    print('started main_thread')
    updater = telegram.ext.Updater(token=TG_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text, add_hashtag))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit("You have to pass in db file path")
    thread_one = threading.Thread(target=start_streaming_tweets)
    thread_one.start()
    start_dispatch()
    thread_one.join()

