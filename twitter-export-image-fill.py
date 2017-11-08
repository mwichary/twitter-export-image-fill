#!/usr/bin/env python

'''
Twitter export image fill 1.03
by Marcin Wichary (aresluna.org)

Site: https://github.com/mwichary/twitter-export-image-fill

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

For more information, please refer to <http://unlicense.org/>
'''

# Imports
# ---------------------------------

import argparse
import json
import os
import re
import stat
import sys
import time
from shutil import copyfile
# The location of urlretrieve changed modules in Python 3
if (sys.version_info > (3, 0)):
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve


# Functions
# ---------------------------------

# Re-save the JSON data back to the original file.
def resave_data(data, data_filename, first_data_line, year_str, month_str):
  # Writing to a separate file so that we can only copy over the
  # main file when done
  data_filename_temp = 'data/js/tweets/%s_%s.js.tmp' % (year_str, month_str)
  with open(data_filename_temp, 'w') as f:
    f.write(first_data_line)
    json.dump(data, f, indent=2)
  os.remove(data_filename)
  os.rename(data_filename_temp, data_filename)


# Downloads an avatar image for a tweet.
# @return Whether data was rewritten
def download_avatar(user):
  # _orig existing means we already processed this user
  if 'profile_image_url_https_orig' in user:
    return False

  avatar_url = user['profile_image_url_https']
  extension = os.path.splitext(avatar_url)[1]
  local_filename = "img/avatars/%s%s" % (user['screen_name'], extension)

  if not os.path.isfile(local_filename):
    # If using an earlier archive as a starting point, try to see if the
    # avatar image is there and can be copied
    if args.EARLIER_ARCHIVE_PATH and os.path.isfile(earlier_archive_path + local_filename):
      copyfile(earlier_archive_path + local_filename, local_filename)

    # Otherwise download it
    else:
      urlretrieve(avatar_url, local_filename)

  user['profile_image_url_https_orig'] = user['profile_image_url_https']
  user['profile_image_url_https'] = local_filename
  return True


# Main entry point
# ---------------------------------

# Introduce yourself

print("Twitter export image fill 1.04")
print("by Marcin Wichary (aresluna.org) and others")
print("use --help to see options")
print("")

# Process arguments

parser = argparse.ArgumentParser(description = 'Downloads all the images to your Twitter archive .')
parser.add_argument('--include-retweets', action='store_true',
    help = 'download images from retweets in addition to your own tweets')
parser.add_argument('--include-videos', dest='PATH_TO_YOUTUBE_DL',
    help = 'output a list of videos to download using youtube_dl (experimental!)')
parser.add_argument('--skip-avatars', action='store_true',
    help = 'do not download avatar images (faster)')
parser.add_argument('--continue-from', dest='EARLIER_ARCHIVE_PATH',
    help = 'use images downloaded into an earlier archive instead of downloading them again (useful for incremental backups)')
parser.add_argument('--verbose', action='store_true',
    help = 'show additional debugging info')
args = parser.parse_args()

include_videos = not not args.PATH_TO_YOUTUBE_DL

# Check whether the earlier archive actually exists
# (This is important because failure would mean quietly downloading all the files again)

if args.EARLIER_ARCHIVE_PATH:
  earlier_archive_path = args.EARLIER_ARCHIVE_PATH
  # Normalizes the slash at the end so it supports both including and not including it
  earlier_archive_path = earlier_archive_path.rstrip('/') + '/'
  if not os.path.isfile(earlier_archive_path + '/data/js/tweet_index.js'):
    print("Could not find the earlier archive!")
    print("Make sure you're pointing at the directory that contains the index.html file.")
    sys.exit()

# Prepare variables etc.

image_count_global = 0
video_count_global = 0
if include_videos:
  video_shell_file_contents = []
if not os.path.isdir("img/avatars"):
  os.mkdir("img/avatars")

# Process the index file to see what needs to be done

index_filename = "data/js/tweet_index.js"
try:
  with open(index_filename) as index_file:
    index_str = index_file.read()
    index_str = re.sub(r'var tweet_index =', '', index_str)
    index = json.loads(index_str)
except:
  print("Could not open the data file!")
  print("Please run this script from your tweet archive directory")
  print("(the one with index.html file).")
  print("")
  sys.exit()

print("To process: %i months worth of tweets..." % (len(index)))
print("(You can cancel any time. Next time you run, the script should resume at the last point.)")
print("")


# Loop 1: Go through all the months
# ---------------------------------

for date in index:
  try:
    year_str = '%04d' % date['year']
    month_str = '%02d' % date['month']
    data_filename = 'data/js/tweets/%s_%s.js' % (year_str, month_str)

    # Make a copy of the original JS file, just in case (only if it doesn't exist before)
    backup_filename = 'data/js/tweets/%s_%s_original.js' % (year_str, month_str)
    if not os.path.isfile(backup_filename):
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

    print("%s/%s: %i tweets to process..." % (year_str, month_str, tweet_length))

    for tweet in data:
      tweet_count = tweet_count + 1
      retweeted = 'retweeted_status' in tweet.keys()

      # Before downloading any images, download an avatar for tweet's author
      # (same for retweet if asked to)
      if not args.skip_avatars:
        data_changed = download_avatar(tweet['user'])

        data_changed_retweet = False
        if args.include_retweets and retweeted:
          data_changed_retweet = download_avatar(tweet['retweeted_status']['user'])

        # Re-save the JSON file if we grabbed any avatars
        if data_changed or data_changed_retweet:
          resave_data(data, data_filename, first_data_line, year_str, month_str)

      # Don't continue with saving images if a retweet (unless forced to)
      if (not args.include_retweets) and retweeted:
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
          # this image or video
          if 'media_url_orig' in media.keys():
            continue

          url = media['media_url_https']
          extension = os.path.splitext(url)[1]

          # Only make the directory when we're ready to write the first file;
          # this will avoid empty directories
          if not os.path.isdir(directory_name):
            os.mkdir(directory_name)

          # Download the original/best image size, rather than the default one
          better_url = url + ':orig'

          local_filename = 'data/js/tweets/%s_%s_media/%s-%s-%s%s%s' %\
              (year_str, month_str, date, tweet['id'], 'rt-' if retweeted else '',
               tweet_image_count, extension)

          can_be_copied = False
          downloaded = False
          download_tries = 3

          # If using an earlier archive as a starting point, try to find the desired
          # image file there first, and copy it if present
          if args.EARLIER_ARCHIVE_PATH and os.path.isfile(earlier_archive_path + local_filename):
            can_be_copied = True

          sys.stdout.write("\r  [%i/%i] %s %s..." %
              (tweet_count, tweet_length, "Copying" if can_be_copied else "Downloading", url))
          sys.stdout.write("\033[K") # Clear the end of the line
          sys.stdout.flush()

          if can_be_copied:
            copyfile(earlier_archive_path + local_filename, local_filename)
          else:
            while not downloaded:
              # Actually download the file!
              try:
                urlretrieve(better_url, local_filename)
              except:
                download_tries = download_tries - 1
                if download_tries == 0:
                  print("")
                  print("Failed to download %s after 3 tries." % better_url)
                  print("Please try again later?")
                  # Output debugging info if needed
                  if args.verbose:
                    print("Debug info: Tweet ID = %s " % tweet['id'])
                  sys.exit()
                time.sleep(5) # Wait 5 seconds before retrying
              else:
                downloaded = True

          # Change the URL so that the archive's index.html will now point to the
          # just-download local file...
          media['media_url_orig'] = media['media_url']
          media['media_url'] = local_filename

          # Re-save the original JSON file every time, so that the script can continue
          # from this point
          resave_data(data, data_filename, first_data_line, year_str, month_str)

          # Test whether this media is actually a video
          is_video = '/video/' in media['expanded_url']
          if is_video:
            video_count_global = video_count_global + 1

            # If the user opted into the experimental way of saving videos...
            if include_videos:
              local_video_filename = 'data/js/tweets/%s_%s_media/%s-%s-video-%s%s.mp4' %\
                  (year_str, month_str, date, tweet['id'], 'rt-' if retweeted else '',
                   tweet_image_count)

              # ...create a shell line to eventually be output into a shell file
              shell_line = '%s %s --exec \'mv {} %s\'' % \
                  (args.PATH_TO_YOUTUBE_DL, media['expanded_url'],
                    local_video_filename.replace(' ', '\ ')) # Don't forget to escape spaces in the filename
              video_shell_file_contents.append(shell_line)

          tweet_image_count = tweet_image_count + 1
          image_count = image_count + 1
          image_count_global = image_count_global + 1

        # End loop 3 (images in a tweet)

    # End loop 2 (tweets in a month)
    sys.stdout.write("\r%s/%s: %i tweets processed; %i images downloaded." % (year_str, month_str, tweet_length, image_count))
    sys.stdout.write("\033[K") # Clear the end of the line
    sys.stdout.flush()
    print("")

  # Nicer support for Ctrl-C
  except KeyboardInterrupt:
    print("")
    print("Interrupted! Come back any time.")
    sys.exit()

# End loop 1 (all the months)
print("")
print("Done!")
print("%i images downloaded in total." % image_count_global)
print("")

# Any videos detected? Tell the user
if video_count_global:
  if include_videos:
    # Output the shell file that can be run to download files using youtube-dl
    video_shell_filename = 'download_videos.sh'
    with open(video_shell_filename, 'w') as f:
      for shell_line in video_shell_file_contents:
        f.write(shell_line)
        f.write("\n")
      f.write("echo \"\nDone downloading videos!\n\"\n")

    # Change the permissions so it's an executable file
    os.chmod(video_shell_filename, stat.S_IREAD + stat.S_IWRITE + stat.S_IXUSR)

    print("A shell file to download %i videos using youtube_dl has been created. Try running:" % video_count_global)
    print("./download_videos.sh")
  else:
    print("%i videos have NOT been downloaded." % video_count_global)
    print("If you want, use the experimental include-videos option to download videos.")
    print("For more info, use --help, or look at https://github.com/mwichary/twitter-export-image-fill")

  print("")
