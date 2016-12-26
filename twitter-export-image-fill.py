#!/usr/bin/python

'''
Twitter export image fill
by Marcin Wichary (aresluna.org)

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

For more information, please refer to <http://unlicense.org/>
'''

import json
import os
import re
import sys
import time
import urllib
from shutil import copyfile

# Introduce yourself

print "Twitter export image fill"
print "by Marcin Wichary (aresluna.org)"
print

image_count_global = 0

# Process the index file to see what needs to be done

index_filename = "data/js/tweet_index.js"
try:
  with open(index_filename) as index_file:
    index_str = index_file.read()
    index_str = re.sub(r'var tweet_index =', '', index_str)
    index = json.loads(index_str)
except:
  print "Could not open the data file!"
  print "Please run this script from your tweet archive directory"
  print "(the one with index.html file)."
  print
  sys.exit()

print "%i months to process..." % (len(index))
print "(You can cancel any time. Next time you run, the script should resume at the last point.)"
print


# Loop 1: Go through all the months
# ---------------------------------

for date in index:
  try:
    year_str = '%04d' % date['year']
    month_str = '%02d' % date['month']
    data_filename = 'data/js/tweets/%s_%s.js' % (year_str, month_str)

    # Make a copy of the original JS file, just in case (only if it doesn't exist before)
    backup_filename = 'data/js/tweets/%s_%s_original.js' % (year_str, month_str)
    try:
      os.stat(backup_filename)
    except:
      copyfile(data_filename, backup_filename)


    # Loop 2: Go through all the tweets in a month
    # --------------------------------------------

    with open(data_filename) as data_file:
      data_str = data_file.read()
      # Remove the assignment to a variable that breaks JSON parsing,
      # but save for later since we have to recreate the file
      first_data_line = re.match(r'Grailbird.data.tweets_(.*) =', data_str).group(0)
      data_str = re.sub(first_data_line, '', data_str)
      data = json.loads(data_str)

    tweet_length = len(data)
    image_count = 0
    tweet_count = 0
    directory_name = 'data/js/tweets/%s_%s_media' % (year_str, month_str)

    print "%s/%s: %i tweets to process..." % (year_str, month_str, tweet_length)

    for tweet in data:
      tweet_count = tweet_count + 1

      # Don't save images from retweets
      if 'retweeted_status' in tweet.keys():
        continue

      if tweet['entities']['media']:
        tweet_image_count = 1

        # Rewrite tweet date to be used in the filename prefix
        # (only first 19 characters + replace colons with dots)
        date = re.sub(r':', '.', tweet['created_at'][:19])


        # Loop 3: Go through all the media in a tweet
        # -------------------------------------------

        for media in tweet['entities']['media']:
          # media_url_orig being present means we already processed/downloaded
          # this file
          if 'media_url_orig' in media.keys():
            continue

          url = media['media_url_https']
          extension = re.match(r'(.*)\.([^.]*)$', url).group(2)

          # Only make the directory when we're ready to write the first file;
          # this will avoid empty directories
          try:
            os.stat(directory_name)
          except:
            os.mkdir(directory_name)

          # Download the original/best image size, rather than the default one
          better_url = url + ':orig'

          local_filename = 'data/js/tweets/%s_%s_media/%s-%s-%s.%s' %\
              (year_str, month_str, date, tweet['id'], tweet_image_count, extension)

          sys.stdout.write("\r  [%i/%i] Downloading %s..." % (tweet_count, tweet_length, url))
          sys.stdout.write("\033[K") # Clear the end of the line
          sys.stdout.flush()

          download_tries = 3
          downloaded = False
          while not downloaded:
            # Download the file!
            try:
              urllib.urlretrieve(better_url, local_filename)
            except:
              download_tries = download_tries - 1
              if download_tries == 0:
                print
                print "Failed to download %s after 3 tries." % better_url
                print "Please try again later?"
                sys.exit()
              time.sleep(5) # Wait 5 seconds before retrying
            else:
              downloaded = True

          # Rewrite the original JSON file so that the archive's index.html
          # will now point to local files... and also so that the script can
          # continue from last point
          media['media_url_orig'] = media['media_url']
          media['media_url'] = local_filename

          # Writing to a separate file so that we can only copy over the
          # main file when done
          data_filename_temp = 'data/js/tweets/%s_%s.js.tmp' % (year_str, month_str)
          with open(data_filename_temp, 'w') as f:
            f.write(first_data_line)
            json.dump(data, f, indent=2)
          os.remove(data_filename)
          os.rename(data_filename_temp, data_filename)

          tweet_image_count = tweet_image_count + 1
          image_count = image_count + 1
          image_count_global = image_count_global + 1

        # End loop 3 (images in a tweet)

    # End loop 2 (tweets in a month)
    sys.stdout.write("\r%s/%s: %i tweets processed; %i images downloaded." % (year_str, month_str, tweet_length, image_count))
    sys.stdout.write("\033[K") # Clear the end of the line
    sys.stdout.flush()
    print

  # Nicer support for Ctrl-C
  except KeyboardInterrupt:
    print
    print "Interrupted! Come back any time."
    sys.exit()

# End loop 1 (all the months)
print
print "Done!"
print "%i images downloaded in total." % image_count_global
print
