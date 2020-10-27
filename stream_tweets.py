import requests
import os
import json
import tweet_db
import time

# To set your enviornment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'


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
        {"value": "(#StopArmenianAggression OR #StopArmenianTerrorism OR #ArmeniaKillsChildren OR #StopArmenianTerror OR @nahidbabayev_ OR @fridah0291 OR @Gunel883 OR @CanAzerbaycan14 OR @Lami80804081 OR @Klepsik OR @jewish66 OR @Elsana__M OR @DrRomeoo OR @Suleyman00717 OR @narminyya OR @1992Aslanl OR @IlkinAkhundlu00 OR @Nika37035074 OR @HashimliSam OR @jaliya__ OR @sadaqatmamadova OR @mihirzali OR @Ulviyya99 OR @wwwmodgovaz OR @presidentaz OR @cavidaga) lang:en"},
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
    try:
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream", headers=headers, stream=True,
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

    except KeyboardInterrupt:
        tweetDb.conn.commit()
        tweetDb.conn.close()
        quit()


def main():
    bearer_token = os.environ.get("TWITTER_AUTH_BEARER_TOKEN")
    headers = create_headers(bearer_token)
    rules = get_rules(headers, bearer_token)
    delete = delete_all_rules(headers, bearer_token, rules)
    set = set_rules(headers, delete, bearer_token)
    tweetDb = tweet_db.TweetDb("tavatirTweets_v2.db")
    get_stream(headers, set, bearer_token, tweetDb)


if __name__ == "__main__":
    main()
