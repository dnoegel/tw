#!/usr/bin/env python2
# coding:utf-8

import os
import argparse
import tweepy
import sys
import simplejson
#http://code.google.com/p/tweepy/wiki/APIReference


## Put Developer-Key and Dev-Secret here
CONSUMER_KEY = "INSERT_HERE"
CONSUMER_SECRET = "INSERT_HERE"

## Config-path
CONFIG = os.path.expanduser("~/.config/tw.cfg")

## Load Config from json-string
try:
    with open(CONFIG, "r") as fh:
        content = fh.read()
        conf = simplejson.loads(content)
except (IOError, simplejson.decoder.JSONDecodeError):
    conf = {u"key":None, u"secret":None, 
        u"latest":{u"search":{}},
        u"short_tweet_ids":[]}

## login and return auth-object
def do_login(conf):

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    if conf[u"key"] and conf[u"secret"]:
        pass
    else:
        url = auth.get_authorization_url()
        print "Sie müssen dieses Programm bei Twitter zunächst freischalten."
        print "Dies ist in zwei Schritten erledigt: \n"
        
        print "1) Öffnen sie diese URL:\n{0}\n".format(url)
        print "2) Schalten sie dieses Programm frei und geben sie die PIN hier ein:"
        pin = ""
        while not pin.isdigit():
            pin = unicode(raw_input("PIN: "))
        auth.get_access_token(pin)
        
        conf[u"key"] = auth.access_token.key
        conf[u"secret"] = auth.access_token.secret
        
        with open(CONFIG, "w") as fh:
            fh.write(simplejson.dumps(conf))
        
    auth.set_access_token(conf[u"key"], conf[u"secret"])
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
def print_tweet(tweet, short_tweet_id, startpos):
    original_tweet = tweet
    try: 
        tweet =  tweet.retweeted_status
        retweet = True
    except AttributeError:
        retweet = False
        
    try:
        author = encode(tweet.from_user_name)
    except AttributeError:
        author = encode(tweet.author.name)
    
    if retweet: 
        print "{0}) {4}: RT @{1} ({time}): \n{2}\n(Tweet ID: {3} | Short Tweet ID: {5})\n".format(startpos, author, encode(tweet.text), tweet.id, encode(original_tweet.author.name), short_tweet_id,time=tweet.created_at)
    else:
        print "{0}) {1}: ({time})\n{2}\n(Tweet ID: {3} | Short Tweet ID: {4})\n".format(startpos, author, encode(tweet.text), tweet.id, short_tweet_id,time=tweet.created_at)
                

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
    query.add_argument('-n', '--new',  help='Only show new tweets', default=False, action='store_true')    
    
    do_tweet = parser.add_argument_group("Tweet options")
    do_tweet.add_argument("-r", '--retweet',  metavar="(Short)TweetID", help='Retweet a given tweet', default=0, action='store', type=int)
    do_tweet.add_argument("-t", '--tweet',  metavar="Message", help='Update status / tweet', default=0, action='store', type=str)
    
    favs = parser.add_argument_group("Favorite options")
    favs.add_argument("-f", '--favorite',  metavar="(Short)TweetID", help='Favorite given Status', default=0, action='store', type=int)
    favs.add_argument('--list-favorites', help='List favorites', default=False, action='store_true')
    
    misc = parser.add_argument_group("Misc options")
    misc.add_argument('-q', '--list-searches',  help='List recent searches', default=False, action='store_true')
    
    args = parser.parse_args()

    ## do login and bind api object
    auth = do_login(conf)
    api = tweepy.API(auth)

    ## if "--latest" was specified, set since_ids to the correct values
    # else set them to None (=no filter)
    if args.new:
        since_home = conf[u"latest"].get(u"home", None)
        since_mentions = conf[u"latest"].get(u"mentions", None)
        since_own = conf[u"latest"].get(u"own", None)
        if args.search and args.search in conf[u"latest"].get(u"search", {}):
            since_search = conf[u"latest"][u"search"][args.search]
        else:
            since_search = None
    else:
        since_home, since_mentions, since_own, since_search = None, None, None, None

    ## base value for tweet-numbers
    startpos = args.count * (args.page-1)
    if args.page <2:
        startpos += 1

    short_tweet_ids = []
    
    #
    # Tweet and retweet
    # 
    
    ## Tweet a message
    if args.tweet:
        try:
            api.update_status(args.tweet)
            print "Tweeted your message"
        except tweepy.error.TweepError, inst:
            print "An error occured: {0}".format(inst)
            sys.exit(3)

    ## Retweet a message
    if args.retweet and args.retweet > 0:
        if  args.retweet < 10000:
            try:
                tweet_id = conf[u"short_tweet_ids"][args.retweet-1]
            except IndexError:
                print "Short Tweet ID not found."
                print "Remember: Short Tweet IDs are only valid for one twcmd session"
                sys.exit(1)
        else:
            tweet_id = args.retweet
        
        print "Retweeting the following tweet: "
        print_tweet(api.get_status(tweet_id), "None", 1)
        api.retweet(tweet_id)

    #
    # Favorites
    #
    
    ## Favorite a message
    if args.favorite and args.favorite > 0:
        if  args.favorite < 10000:
            try:
                tweet_id = conf[u"short_tweet_ids"][args.favorite-1]
            except IndexError:
                print "Short Tweet ID not found."
                print "Remember: Short Tweet IDs are only valid for one twcmd session"
                sys.exit(5)
        else:
            tweet_id = args.favorite
        
        print "Favoriting the following tweet: "
        print_tweet(api.get_status(tweet_id), "None", 1)
        api.create_favorite(tweet_id)

    ## List favorites
    if args.list_favorites:
        print "Favorites:"
        print "=========="
        for i, tweet in r_enumerate(api.favorites(page=args.page, count=args.count)):
            short_tweet_ids.append(tweet.id)
            print_tweet(tweet, len(short_tweet_ids), i+startpos)


    #
    # Different list modes
    #

    if args.list_searches:
        print "Recent Searches:"
        print "================"
        for i, search in enumerate(conf[u"latest"].get(u"search", {})):
            print "{0}) {1}".format(i+1, search)

    ## process the different tweet-modes
    if args.home:
        print "Home Tweets:"
        print "============"
        for i, tweet in r_enumerate(api.home_timeline(since_id=since_home,page=args.page, count=args.count)):
            short_tweet_ids.append(tweet.id)
            print_tweet(tweet, len(short_tweet_ids), i+startpos)
            #~ conf["latest_home"] = tweet.id
            conf[u"latest"][u"home"] = tweet.id
    
    if args.mentions:
        print "Mentions:"
        print "========="
        for i, tweet in r_enumerate(api.mentions(since_id=since_mentions, page=args.page, count=args.count)):
            short_tweet_ids.append(tweet.id)
            print_tweet(tweet, len(short_tweet_ids), i+startpos)
            
            conf[u"latest"][u"mentions"] = tweet.id
            #~ conf["latest_mentions"] = tweet.id
    
    if args.own:
        print "Own tweets:"
        print "==========="
        for i, tweet in r_enumerate(api.user_timeline(include_rts=1,since_id=since_own, page=args.page, count=args.count)):
            short_tweet_ids.append(tweet.id)
            print_tweet(tweet, len(short_tweet_ids), i+startpos)
            
            conf[u"latest"][u"own"] = tweet.id
            #~ conf["latest_own"] = tweet.id
            
    if args.search:
        print "Search tweets"
        print "============="
        for i, result in r_enumerate(api.search(q=args.search,since_id=since_search, page=args.page, rpp=args.count)):
            short_tweet_ids.append(result.id)
            print_tweet(result, len(short_tweet_ids), i+startpos)
            
            conf[u"latest"][u"search"][args.search.lower()] = result.id

    ## Store short tweet ids into the config-dict
    conf[u"short_tweet_ids"] = short_tweet_ids
    
    ## write back config-object
    with open(CONFIG, "w") as fh:
        fh.write(simplejson.dumps(conf))
