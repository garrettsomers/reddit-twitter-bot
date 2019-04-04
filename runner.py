import os
import time
import datetime

NumSeconds = 3600*8

i = 1
while True:

#	now = datetime.datetime.now()
#	then = now + datetime.timedelta(seconds=NumSeconds)
#	print '[gbot] The next post will be at', then, '\n\n'
#	time.sleep(NumSeconds)

	os.system('python reddit_twitter_bot.py')

	now = datetime.datetime.now()
	then = now + datetime.timedelta(seconds=NumSeconds)
	print '[gbot] The next post will be at', then, '\n\n'
	time.sleep(NumSeconds)

	print '[gbot] loop time! loop number', i
	i += 1
