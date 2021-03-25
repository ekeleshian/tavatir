# tavatir

A repo that collects and analyzes anti-Armenian tweets. 

*PreRequisites*: Getting a Bearer Token from twitter's dev site and an access token from telegram for a new bot. Store those as env vars in your bash profile.

### Getting started
1. git clone https://github.com/ekeleshian/tavatir.git
2. install dependencies
```bash
$ cd tavatir
$ virtualenv -p python3 env
$ source env/bin/activate
$ cat requirements.txt | xargs -n 1 -L 1 pip install
``` 
3. start up sqlite3 console to open new db
```bash
$ mkdir data
$ sqlite3
> .open data/tavatirTweets_v1.db
> .quit
```

4. Move to Section "Online Stream Handling"


## Online Stream Handling
*how to start up a program that collects a live stream of tweets*

`$ python stream.py tavatirTweets_v1.db`

### Telegram Service

The twitter livestream is configured to filter by hashtags, hardcoded at first, but will programmatically change when the
bot pings user of highly frequented hashtags and user pings bot back whether or not said hashtags should be added to the filter.



## Offline Data Analysis
*how to generate useful tweet visualizations from stored tweets*

1.  `$ python pipeline.py`  # clean up tweets
2. `$ python app.py` # start up local dashboard