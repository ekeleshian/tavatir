import csv
import json
import time
import sqlite3
from sqlite3 import Error
from datetime import datetime
from pdb import set_trace


class TweetDb:
    def __init__(self, db_file="tavatirTweets.db"):
        def create_tables():
            sql1 = """
            CREATE TABLE IF NOT EXISTS tweet ( 
                id INTEGER PRIMARY KEY,
                matching_rules_ids text,
                content text,
                content_id text,
                received_at text
            );
            """

            try:
                self.cursor.execute(sql1)
                self.conn.commit()
                print("tweet TABLE created.")

            except Error as e:
                self.conn.rollback()
                print(e)

        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.size = 0
        create_tables()

    def insert(self, data):
        data = json.loads(data)
        content = data.get('data', {}).get('text', '')
        if content:
            content_id = data['data']['id']
            matching_rules_ids = []
            for mr in data['matching_rules']:
                matching_rules_ids.append(mr['id'])
            matching_rules_ids_str = json.dumps(matching_rules_ids)
            time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            sql = "INSERT INTO tweet (content, content_id, matching_rules_ids, received_at) VALUES (?, ?, ?, ?)"

            self.cursor.execute(sql, (content, content_id, matching_rules_ids_str, time))

            self.conn.commit()
            self.size += 1
            curr_idx = int(self.size / 100)

            if self.size == curr_idx * 100:
                print(self.size)

        else:
            print(f"content not found in data: {data}")

    def save(self, path=""):
        sql = "SELECT * FROM tweet"

        if not path:
            path = f"data/tweets_{str(time.time())}.csv"

        with open(path, "wb") as write_file:

            for row in self.cursor.execute(sql):
                writeRow = " ".join(row)
                write_file.write(writeRow.encode())

        return f"Saved CSV to {path}"




