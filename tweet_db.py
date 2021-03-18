import csv
import json
import time
import sqlite3
from sqlite3 import Error
from datetime import datetime

class TweetDb:
    def __init__(self, db_file="tavatirTweets_v2.db", should_create_tables=False):
        def create_tables():
            sql1 = """
            CREATE TABLE tweet ( 
                id INTEGER PRIMARY KEY,
                matching_rules_ids text,
                content text,
                content_id text,
                received_at text,
                user_id text,
                username text,
                possibly_sensitive BOOLEAN,
                place_name text,
                place_id text,
                urls text,
                referenced_tweets text
            );
            """

            try:
                self.cursor.execute(sql1)
                self.conn.commit()

            except Error as e:
                self.conn.rollback()
                print(e)

        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        if should_create_tables:
            create_tables()
            print("tweet table created.\n")

    def insert(self, data):
        data = json.loads(data)
        content = data.get('data', {}).get('text', '')
        user_id = ""
        username = ""
        place_name = ""
        place_id = ""
        if content:
            content_id = data['data']['id']
            possibly_sensitive = data['data']["possibly_sensitive"]
            for field in data['includes']:
                if field == 'users':
                    user_id = data['includes'][field][0]['id']
                    username = data['includes'][field][0]['username']
                if field == "places":
                    place_name = data['includes'][field][0]['full_name']
                    place_id = data['includes'][field][0]['id']

            urls = []
            if data['data']['entities'].get("urls"):
                for url in data['data']['entities']['urls']:
                    urls.append(url['expanded_url'])
            urls_str = json.dumps(urls)

            matching_rules_ids = []
            for mr in data['matching_rules']:
                matching_rules_ids.append(mr['id'])
            matching_rules_ids_str = json.dumps(matching_rules_ids)

            referenced_tweets = []
            if data['data'].get("referenced_tweets"):
                for rf in data['data']['referenced_tweets']:
                    referenced_tweets.append(rf['id'])
            referenced_tweets_str = json.dumps(referenced_tweets)
            time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            sql = "INSERT INTO tweet (content, content_id, matching_rules_ids, received_at, user_id, username, place_name, place_id, possibly_sensitive, urls, referenced_tweets) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

            self.cursor.execute(sql, (content, content_id, matching_rules_ids_str, time, user_id, username, place_name, place_id, possibly_sensitive, urls_str, referenced_tweets_str))

            self.conn.commit()

        else:
            print(f"content not found in data: {data}")

    def save(self, path="", version=''):
        sql = "SELECT * FROM tweet"

        if not path:
            path = f"data/tavatirTweetsRaw{version}.csv"

        with open(path, "w") as write_file:
            rows = self.cursor.execute(sql).fetchall()
            csv_out = csv.writer(write_file)
            csv_out.writerow(['id', 'matching_rules_ids', 'content', 'content_id', 'received_at', "user_id", "username",
                              "possibly_sensitive", "place_name", "place_id", "urls", 'referenced_tweets'])
            for row in rows:
                new_row = tuple([str(v) if idx == 0 else v for idx, v in enumerate(row)])
                csv_out.writerow(new_row)


        return f"Saved CSV to {path}"
