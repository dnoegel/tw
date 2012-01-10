#!/usr/bin/env python2
# coding:utf-8

import os
import argparse
import tweepy
import sys
import simplejson
#http://code.google.com/p/tweepy/wiki/APIReference


CONFIG = os.path.expanduser("~/.config/tw.cfg")

CONSUMER_KEY = "HUksGUHzty6Zz521xhV8GA"
CONSUMER_SECRET = "dler0WgFKWPn3IkTF076RxbEnvfNqPeyUwvxu0WnwY"

## Load Config from json-string
try:
    with open(CONFIG, "r") as fh:
        content = fh.read()
        conf = simplejson.loads(content)
except (IOError, simplejson.decoder.JSONDecodeError):
    conf = {"key":None, "secret":None, 
        "latest_home":None, "latest_mentions":None, "latest_own":None, "latest_search":{},
        "short_tweet_ids":[]}

## login and return auth-object
def do_login(conf):

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    if conf["key"] and conf["secret"]:
        pass
    else:
        url = auth.get_authorization_url()
        print "Sie müssen dieses Programm bei Twitter zunächst freischalten."
        print "Dies ist in zwei Schritten erledigt: \n"
        
        print "1) Öffnen sie diese URL:\n{0}\n".format(url)
        print "2) Schalten sie dieses Programm frei und geben sie die PIN hier ein:"
        pin = ""
        while not pin.isdigit():
            pin = raw_input("PIN: ")
        auth.get_access_token(pin)
        
        conf["key"] = auth.access_token.key
        conf["secret"] = auth.access_token.secret
        
        with open(CONFIG, "w") as fh:
            fh.write(simplejson.dumps(conf))
        
    auth.set_access_token(conf["key"], conf["secret"])
    
    return auth

## returns utf-8 encoded text
def encode(txt, encoding=sys.stdout.encoding):
    return txt.encode(encoding)

## reverse enumeration
def r_enumerate(container):
    i = len(container)
    for item in reversed(container):
        i = i - 1
        yield i, item

## Print a tweet
def print_tweet(tweet, short_tweet_id, startpos, is_result=False):
    original_tweet = tweet
    try: 
        tweet =  tweet.retweeted_status
        retweet = True
    except AttributeError:
        retweet = False
        
    if is_result:
        author = encode(tweet.from_user_name)
    else:
        author = encode(tweet.author.name)
    
    if retweet: 
        print "{0}) {4}: RT @{1}: \n{2}\n(Tweet ID: {3} | Short Tweet ID: {5})\n".format(startpos, author, encode(tweet.text), tweet.id, encode(original_tweet.author.name), short_tweet_id)
    else:
        print "{0}) {1}: \n{2}\n(Tweet ID: {3} | Short Tweet ID: {4})\n".format(startpos, author, encode(tweet.text), tweet.id, short_tweet_id)
                

if __name__ == "__main__":
    ## Arg parse related stuff
    parser = argparse.ArgumentParser(description='tw - simple twitter commandline tool')
    
    ops = parser.add_argument_group("Operations")
    ops.add_argument('-l', '--home', '--timeline',  help='Show your home timeline', default=False, action='store_true')
    ops.add_argument('-m', '--mentions',  help='Show your mentions', default=False, action='store_true')
    ops.add_argument('-o', '--own',  help='Show your own tweets', default=False, action='store_true')
    ops.add_argument('-s', '--search',  help='Search a tweet', default=None, action='store')

    query = parser.add_argument_group("Query options")
    query.add_argument("-c", '--count',  help='Number of tweets to fetch. Default: 20 Max: 200', default=20, action='store', type=int)
    query.add_argument("-p", '--page',  help='Page to start from. Default: 0', default=1, action='store', type=int)
    ops.add_argument('-n', '--new',  help='Only show new tweets', default=False, action='store_true')
    
    do_tweet = parser.add_argument_group("Tweet options")
    do_tweet.add_argument("-r", '--retweet',  metavar="(Short)TweetID", help='Retweet a given tweet', default=0, action='store', type=int)
    do_tweet.add_argument("-t", '--tweet',  metavar="Message", help='Update status / tweet', default=0, action='store', type=str)
    
    args = parser.parse_args()

    ## do login and bind api object
    auth = do_login(conf)
    api = tweepy.API(auth)

    ## if "--latest" was specified, set since_ids to the correct values
    # else set them to None (=no filter)
    if args.new:
        since_home = conf["latest_home"]
        since_mentions = conf["latest_mentions"]
        since_own = conf["latest_own"]
        if args.search and args.search in conf["latest_search"]:
            since_search = conf["latest_search"][args.search]
        else:
            since_search = None
    else:
        since_home, since_mentions, since_own, since_search = None, None, None, None

    ## base value for tweet-numbers
    startpos = args.count * (args.page-1)
    if args.page <2:
        startpos += 1

    short_tweet_ids = []
    
    if args.tweet:
        if len(args.tweet)>140:
            print "Message to long ({0}/140)".format(len(args.tweet))
            sys.exit(2)
        else:
            try:
                print api.update_status(args.tweet)
            except tweepy.error.TweepError, inst:
                print "An error occured: {0}".format(inst)
                sys.exit(3)
            

    ## Retweet a message
    if args.retweet and args.retweet > 0:
        if  args.retweet < 10000:
            try:
                tweet_id = conf["short_tweet_ids"][args.retweet-1]
            except IndexError:
                print "Short Tweet ID not found."
                print "Remember: Short Tweet IDs are only valid for one twcmd session"
                sys.exit(1)
        else:
            tweet_id = args.retweet
        
        print "Retweeting the following tweet: "
        print_tweet(api.get_status(tweet_id), "None", 1)
        api.retweet(tweet_id)

    ## process the different tweet-modes
    if args.home:
        print "Home Tweets:"
        print "============"
        for i, tweet in r_enumerate(api.home_timeline(since_id=since_home,page=args.page, count=args.count)):
            short_tweet_ids.append(tweet.id)
            print_tweet(tweet, len(short_tweet_ids), i+startpos)
            conf["latest_home"] = tweet.id
    
    if args.mentions:
        print "Mentions:"
        print "========="
        for i, tweet in r_enumerate(api.mentions(since_id=since_mentions, page=args.page, count=args.count)):
            short_tweet_ids.append(tweet.id)
            print_tweet(tweet, len(short_tweet_ids), i+startpos)
            
            conf["latest_mentions"] = tweet.id
    
    if args.own:
        print "Own tweets:"
        print "==========="
        for i, tweet in r_enumerate(api.user_timeline(include_rts=1,since_id=since_own, page=args.page, count=args.count)):
            short_tweet_ids.append(tweet.id)
            print_tweet(tweet, len(short_tweet_ids), i+startpos)
            
            conf["latest_own"] = tweet.id
            
    if args.search:
        print "Search tweets"
        print "============="
        for i, result in r_enumerate(api.search(q=args.search,since_id=since_search, page=args.page, rpp=args.count)):
            short_tweet_ids.append(result.id)
            print_tweet(result, len(short_tweet_ids), i+startpos, is_result=True)
            
            conf["latest_search"][args.search] = result.id

    ## Store short tweet ids into the config-dict
    conf["short_tweet_ids"] = short_tweet_ids
    
    ## write back config-object
    with open(CONFIG, "w") as fh:
        fh.write(simplejson.dumps(conf))
