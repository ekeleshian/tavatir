import requests
import os
from pdb import set_trace
import pickle


"https://api.twitter.com/2/users/by/username/:username"


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def get_user_by_username(name, headers):
    return requests.get(f"https://api.twitter.com/2/users/by/username/{name}", headers=headers)


def get_user_ids_by_usernames(usernames_str, save=True, version='_v6'):
    bearer_token = os.environ.get("SECOND_TWITTER_AUTH_BEARER_TOKEN")
    headers = create_headers(bearer_token)
    usernames = usernames_str.split(" OR ")
    user_ids = []
    for name in usernames:
        username = name[1:]
        response = get_user_by_username(username, headers)
        if response.status_code == 200:
            object_data = response.json()
            user_ids.append(object_data['data']['id'])
    if save:
        with open(f"data/user_id_list{version}.pkl", 'wb') as file:
            pickle.dump(user_ids, file)


def get_followers_by_user_id(user_id, follower_ids):
    bearer_token = os.environ.get("SECOND_TWITTER_AUTH_BEARER_TOKEN")
    headers = create_headers(bearer_token)
    response = requests.get(f"https://api.twitter.com/1.1/followers/ids.json?user_id={user_id}", headers=headers)
    if response.status_code == 200:
        object_data = response.json()
        followers = object_data['ids'] #list of integer ids
        while object_data['next_cursor'] != 0:
            response = requests.get(f"https://api.twitter.com/1.1/followers/ids.json?user_id={user_id}&cursor={object_data.next_cursor_str}", headers=headers)
            if response.status_code == 200:
                object_data = response.json()
                followers.extend(object_data['ids'])
            else:
                break
        follower_ids.append(followers)
    else:
        set_trace()
        follower_ids.append([])
    return follower_ids


def main():
    user_ids = []
    follower_ids = []
    usernames_str = "@nahidbabayev_ OR @fridah0291 OR @Gunel883 OR @CanAzerbaycan14 OR @Lami80804081 OR @Klepsik OR @jewish66 OR @Elsana__M OR @DrRomeoo OR @Suleyman00717 OR @narminyya OR @1992Aslanl OR @IlkinAkhundlu00 OR @Nika37035074 OR @HashimliSam OR @jaliya__ OR @sadaqatmamadova OR @mihirzali OR @Ulviyya99 OR @wwwmodgovaz OR @presidentaz OR @cavidaga "

    try:
        with open(f"data/user_id_list.pkl", 'rb') as file:
            user_ids = pickle.load(file)
    except:
        user_ids = get_user_ids_by_usernames(usernames_str)

    for idx, user_id in enumerate(user_ids):
        if idx > 18: #followers will explode on president and cavid
            follower_ids.append([])
        else:
            follower_ids = get_followers_by_user_id(user_id, follower_ids)

    with open('data/follower_ids.pkl', 'wb') as file:
        pickle.dump(follower_ids, file)



if __name__ == '__main__':
    main()