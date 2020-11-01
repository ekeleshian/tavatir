import requests
import os
from pdb import set_trace
import pickle
import pandas as pd
import re


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def get_tweet_by_url(url, headers):
    response = requests.get(f"https://api.twitter.com/1.1/search/tweets.json?q={url}", headers=headers)
    return response

def findall_urls(text):
    result= re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", text)
    if len(result) == 0:
        return 0
    return result


def get_tweet_by_id(id, headers):
    response = requests.get(f"https://api.twitter.com/2/tweets/{id}", headers=headers)
    return response


def main():
    bearer_token = os.environ.get("SECOND_TWITTER_AUTH_BEARER_TOKEN")
    headers = create_headers(bearer_token)
    df_all = pd.read_csv("data/tavatirTweetsProcessed_83715.csv")
    df_all['urls'] = df_all['content'].apply(findall_urls)
    urls = list(df_all[df_all['urls'] != 0]['urls'])
    df_urls_index = list(df_all[df_all['urls'] != 0]['urls'].index)
    df_all['url_content'] = ''

    for idx, url_arr in enumerate(urls):
        for url in url_arr:
            response = get_tweet_by_url(url, headers=headers)
            if response.status_code == 200:
                object_data = response.json()
                while len(object_data['statuses']) == 0:
                    tweet_id = object_data['search_metadata']['max_id']
                    tweet_response = get_tweet_by_id(tweet_id, headers)
                    if tweet_response.status_code == 200:
                        new_object_data = tweet_response.json()
                        if not new_object_data.get('errors'):
                            df_idx = df_urls_index[idx]
                            df_all.at[df_idx, 'url_content'] = new_object_data['data']['text']
                        else:
                            break
                    else:
                        print(tweet_response.reason)
                        break
        break



    df_all.to_csv("data/tavatirTweetsProcessed_v7.csv", index=False )



if __name__ == '__main__':
    main()




