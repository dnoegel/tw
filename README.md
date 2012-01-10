tw
==

A simple twitter terminal client

Usage
-----
usage: tw [-h] [-l] [-m] [-o] [-s SEARCH] [-c COUNT] [-p PAGE] [-n]
          [-r ShortTweetID] [-t Message]

tw - simple twitter commandline tool

optional arguments:
  -h, --help            show this help message and exit

Operations:
  -l, --home, --timeline
                        Show your home timeline
  -m, --mentions        Show your mentions
  -o, --own             Show your own tweets
  -s SEARCH, --search SEARCH
                        Search a tweet
  -n, --new             Only show new tweets

Query options:
  -c COUNT, --count COUNT
                        Number of tweets to fetch. Default: 20 Max: 200
  -p PAGE, --page PAGE  Page to start from. Default: 0

Tweet options:
  -r (Short)TweetID, --retweet (Short)TweetID
                        Retweet a given tweet
  -t Message, --tweet Message
                        Update status / tweet

