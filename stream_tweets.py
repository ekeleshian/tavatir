import requests
import os
import sys
import json
import tweet_db
import time
from datetime import datetime


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def get_rules(headers, bearer_token):
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", headers=headers
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print(json.dumps(response.json()))
    return response.json()


def delete_all_rules(headers, bearer_token, rules):
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


def set_rules(headers, delete, bearer_token):
    # You can adjust the rules if needed
    sample_rules = [
        {"value": "(#StopArmenianAggression OR #ArmenianMilitaryCoup OR #ArmenianGovernmentTrolls OR #StopArmenianTerrorism OR #babykillerarmenia OR #WakeUpArmenia 1OR #ArmeniaKillsChildren OR #StopArmenianTerror OR #KarabakhisAzerbaijan OR #Azerbaijanphobia OR #DontBelieveArmenia OR #StopArmenianLies) lang:en"},
    ]
    payload = {"add": sample_rules}
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


def get_stream(headers, set, bearer_token, tweetDb):
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

            for response_line in response.iter_lines():
                if response_line:
                    json_response = json.loads(response_line)
                    object_data = json.dumps(json_response, indent=4, sort_keys=True)
                    print(object_data)
                    tweetDb.insert(object_data)
                    duration = round(time.time()) - start_time
                    if duration > 2*60*60: #restarts 
                        response.close()
                        print('Closing response....\n')
                        time.sleep(60)
                        now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        print(f'Sleeping done. Calling again at {now}.\n')
                        main() 

        except KeyboardInterrupt:
            tweetDb.conn.commit()
            tweetDb.conn.close()
            quit()


def main():
    bearer_token = os.environ.get("TWITTER_AUTH_BEARER_TOKEN")
    headers = create_headers(bearer_token)
    rules = get_rules(headers, bearer_token)
    delete = delete_all_rules(headers, bearer_token, rules)
    set_ = set_rules(headers, delete, bearer_token)
    tweetDb = tweet_db.TweetDb(db_file=sys.argv[1], should_create_tables=True)
    get_stream(headers, set_, bearer_token, tweetDb)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit("You have to pass in db file path")
    main()
