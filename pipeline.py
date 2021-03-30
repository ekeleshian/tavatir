from os import listdir
from os.path import isfile, join
import tweet_db
import preprocess_tweet
import eda


if __name__ == "__main__":
    dbs = [db for db in listdir('data/db') if isfile(join('data/db', db))]
    print(f'saving {dbs} databases to csv')
    for db in dbs:
        tweetDb = tweet_db.TweetDb(db_file=f'data/db/{db}')
        version = db.split('.')[0].split('_')[-1]
        tweetDb.save(version=f'_{version}')
    print(f'listing data directory:\n{listdir("data")}')

    preprocess_tweet.main(len(dbs))
    print('\nfinished preprocessing tweets....')
    df = eda.main()
    df.to_csv('data/tavatirTweetsTSNE_v4.csv')
