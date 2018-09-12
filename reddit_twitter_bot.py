# -*- coding: utf-8 -*-

'''
Copyright 2015 Randal S. Olson

This file is part of the reddit Twitter Bot library.

The reddit Twitter Bot library is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

The reddit Twitter Bot library is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
License for more details. You should have received a copy of the GNU General
Public License along with the reddit Twitter Bot library.
If not, see http://www.gnu.org/licenses/.
'''

import praw
import json
import requests
import tweepy
import time
import os
from PIL import Image

## My python 2 doesn't have urllib, so use urlparse.urlsplit instead.
#import urllib.parse
from urlparse import urlsplit
from glob import glob

## Read in the Twitter and API keys.
lines = open('../TheKeys.txt').readlines()
for line in lines:
	exec(line)

## This defines:
	## Twitter API keys
	## ACCESS_TOKEN
	## ACCESS_TOKEN_SECRET
	## CONSUMER_KEY
	## CONSUMER_SECRET
	##
	## Reddit API keys
	## REDDIT_KEY
	## REDDIT_SECRET
	## APP_NAME
	## MYUSERAGENT

# Place the subreddit you want to look up posts from here
SUBREDDIT_TO_MONITOR = 'youbelongwithmemes'

# Place the name of the folder where the images are downloaded
IMAGE_DIR = 'img'

# Place the name of the file to store the IDs of posts that have been posted
POSTED_CACHE = 'posted_posts.txt'

# Place the string you want to add at the end of your tweets (can be empty)
TWEET_SUFFIX = ' #TaylorSwift'

# Place the maximum length for a tweet
TWEET_MAX_LEN = 250

# Place the time you want to wait between each tweets (in seconds)
DELAY_BETWEEN_TWEETS = 20

# Place the lengths of t.co links (cf https://dev.twitter.com/overview/t.co)
T_CO_LINKS_LEN = 24

def setup_connection_reddit(subreddit):
    ''' Creates a connection to the reddit API. '''
    print('[bot] Setting up connection with reddit')
    ## Added 
#    reddit_api = praw.Reddit('reddit Twitter tool monitoring {}'.format(subreddit))
    reddit_api = praw.Reddit(client_id=REDDIT_KEY,
                     client_secret=REDDIT_SECRET,
                     user_agent=MYUSERAGENT)
    return reddit_api.get_subreddit(subreddit)


def tweet_creator(subreddit_info):
    ''' Looks up posts from reddit and shortens the URLs to them. '''
    post_dict = {}
    post_ids = []

    print('[bot] Getting posts from reddit')

    # You can use the following "get" functions to get posts from reddit:
    #   - get_top(): gets the most-upvoted posts (ignoring post age)
    #   - get_hot(): gets the most-upvoted posts (taking post age into account)
    #   - get_new(): gets the newest posts
    #
    # "limit" tells the API the maximum number of posts to look up

    indi = 0
    AllSubs = subreddit_info.get_new(limit=200)
        ## Insert a switch to accept post iif it has 5 or more upvotes.
		num_votes = float(str(submission).rsplit('::')[0])
        EnoughVotes = (num_votes >= 5.)
        if not EnoughVotes:
            print('[bot] Not enough upvotes yet for: {}'.format(str(submission)))
            continue
        if not already_tweeted(submission.id):
            indi += 1
     	    if indi == 2: break
            # This stores a link to the reddit post itself
            # If you want to link to what the post is linking to instead, use
            # "submission.url" instead of "submission.permalink"
            post_dict[submission.title] = {}
            post = post_dict[submission.title]
            post['link'] = submission.permalink

            # Store the url the post points to (if any)
            # If it's an imgur URL, it will later be downloaded and uploaded alongside the tweet
            post['img_path'] = get_image(submission.url)
            
            ## Check that the file is less than 4.5 MB
            if float(os.path.getsize(post['img_path'])) > 4500000.:
            	print('[bot] File too big. Resizing')
            	Resizer = 0.5
            	TooBig = True
            	while(TooBig):
            	    ## Open file and halve the width/length
            	    test_img = Image.open(post['img_path'])
            	    width, height = test_img.size
            	    width = int(width*Resizer)
            	    height = int(height*Resizer)
            	    new_img = test_img.resize((width,height))
            	    filetype = post['img_path'].rsplit('.')[-1]
            	    newimg_path = post['img_path'].replace('.','_resized.')
            	    new_img.save(newimg_path,filetype)
            	    ## Check if the new image is now small enough.
            	    if float(os.path.getsize(newimg_path)) > 4500000.:
            	    	## Not small enough. Resize again.
            	    	Resizer = Resizer * 0.5
            	    	print('[bot] First resize not enough. Trying again')
            	    else:
            	    	## Image is now small enough.
            	    	post['img_path'] = newimg_path
            	    	TooBig = False
            	    	print '[bot] File reduced in size by', Resizer
            post_ids.append(submission.id)
            break
        else:
            print('[bot] Already tweeted: {}'.format(str(submission)))
            continue

    return post_dict, post_ids


def already_tweeted(post_id):
    ''' Checks if the reddit Twitter bot has already tweeted a post. '''
    found = False
    with open(POSTED_CACHE, 'r') as in_file:
        for line in in_file:
            if post_id in line:
                found = True
                break
    return found


def strip_title(title, num_characters):
    ''' Shortens the title of the post to the 140 character limit. '''

    # How much you strip from the title depends on how much extra text
    # (URLs, hashtags, etc.) that you add to the tweet
    # Note: it is annoying but some short urls like "data.gov" will be
    # replaced by longer URLs by twitter. Long term solution could be to
    # use urllib.parse to detect those.
    if len(title) <= num_characters:
        return title
    else:
        return title[:num_characters - 1] + '…'


def get_image(img_url):
    ''' Downloads i.imgur.com images that reddit posts may point to. '''
    if 'imgur.com' in img_url or 'i.redd.it' in img_url:
		## Use urlparse instead of urllib.parse
#        file_name = os.path.basename(urllib.parse.urlsplit(img_url).path)
        file_name = os.path.basename(urlsplit(img_url).path)
        img_path = IMAGE_DIR + '/' + file_name
        print('[bot] Downloading image at URL ' + img_url + ' to ' + img_path)
        resp = requests.get(img_url, stream=True)
        if resp.status_code == 200:
            with open(img_path, 'wb') as image_file:
                for chunk in resp:
                    image_file.write(chunk)
            # Return the path of the image, which is always the same since we just overwrite images
            return img_path
        else:
            print('[bot] Image failed to download. Status code: ' + resp.status_code)
    else:
        print('[bot] Post doesn\'t point to an i.imgur.com link')
    return ''


def tweeter(post_dict, post_ids):
    ''' Tweets all of the selected reddit posts. '''
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    for post, post_id in zip(post_dict, post_ids):
        img_path = post_dict[post]['img_path']

        extra_text = ' ' + post_dict[post]['link'] + TWEET_SUFFIX
        extra_text_len = 1 + T_CO_LINKS_LEN + len(TWEET_SUFFIX)
        if img_path:  # Image counts as a link
            extra_text_len += T_CO_LINKS_LEN
        post_text = strip_title(post, TWEET_MAX_LEN - extra_text_len) + extra_text
        print('[bot] Posting this link on Twitter')
        print(post_text)
        if img_path:
            print('[bot] With image ' + img_path)
            api.update_with_media(filename=img_path, status=post_text)
        else:
            api.update_status(status=post_text)
        log_tweet(post_id)
        time.sleep(DELAY_BETWEEN_TWEETS)


def log_tweet(post_id):
    ''' Takes note of when the reddit Twitter bot tweeted a post. '''
    with open(POSTED_CACHE, 'a') as out_file:
        out_file.write(str(post_id) + '\n')


def main():
    ''' Runs through the bot posting routine once. '''
    # If the tweet tracking file does not already exist, create it
    if not os.path.exists(POSTED_CACHE):
        with open(POSTED_CACHE, 'w'):
            pass
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
    post_dict, post_ids = tweet_creator(subreddit)
    tweeter(post_dict, post_ids)

    # Clean out the image cache
    for filename in glob(IMAGE_DIR + '/*'):
        os.remove(filename)

if __name__ == '__main__':
    main()
