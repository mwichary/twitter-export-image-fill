#!/usr/bin/env python

'''
Twitter export image fill 1.07
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


def parse_arguments():
  parser = argparse.ArgumentParser(description = 'Downloads all the images to your Twitter archive .')
  parser.add_argument('--include-videos', dest='PATH_TO_YOUTUBE_DL',
      help = 'use youtube_dl to download videos (and animated GIFs) in addition to images')
  parser.add_argument('--skip-avatars', action='store_true',
      help = 'do not download avatar images (faster)')
  parser.add_argument('--skip-retweets', action='store_true',
      help = 'do not download images or videos from retweets (faster)')
  parser.add_argument('--skip-images', action='store_true',
      help = 'do not download images in general')
  parser.add_argument('--skip-videos', action='store_true',
      help = 'do not download videos (and animated GIFs) in general')
  parser.add_argument('--continue-from', dest='EARLIER_ARCHIVE_PATH',
      help = 'use images downloaded into an earlier archive instead of downloading them again (useful for incremental backups)')
  parser.add_argument('--verbose', action='store_true',
      help = 'show additional debugging info')
  parser.add_argument('--force-download', action='store_true',
      help = 'force to re-download images and videos that were already downloaded')
  return parser.parse_args()


def find_youtube_dl():
  if not args.skip_videos:
    if args.PATH_TO_YOUTUBE_DL:
      if not os.path.isfile(args.PATH_TO_YOUTUBE_DL):
        print("Could not find youtube-dl executable.")
        print("Make sure you're pointing at the right file.")
        print("A typical path would be: /usr/local/bin/youtube-dl")
        sys.exit(-1)

      return True, args.PATH_TO_YOUTUBE_DL
    else:
      if os.path.isfile('/usr/local/bin/youtube-dl'):
        if args.verbose:
          print("(Found youtube-dl automatically.)")
          print("")
        return True, '/usr/local/bin/youtube-dl'
  return False, ''


def load_tweet_index():
  index_filename = "data/js/tweet_index.js"
  try:
    with open(index_filename) as index_file:
      index_str = index_file.read()
      index_str = re.sub(r'var tweet_index =', '', index_str)
      return json.loads(index_str)
      
  except:
    print("Could not open the data file!")
    print("Please run this script from your tweet archive directory")
    print("(the one with index.html file).")
    print("")
    sys.exit(-1)


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


# Download a given image directly from the URL
def download_image(url, local_filename):
  if not download_images:
    return True

  try:
    urlretrieve(url, local_filename)
    return True
  except:
    return False


# Download a given video via youtube-dl
def download_video(url, local_filename):
  if not download_videos:
    return True

  try:
    local_filename_escaped = local_filename.replace(' ', '\ ')
    command = '%s -q --no-warnings %s --exec \'mv {} %s\' &>/dev/null' % \
        (youtube_dl_path, url, local_filename_escaped)
    if os.system(command) > 0:
      return False
    if os.path.isfile(local_filename):
      return True
    else:
      return False
  except:
    return False


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
      try:
        urlretrieve(avatar_url, local_filename)
      except:
        # Okay to quietly fail, this is just an avatar
        # (And, apparently, some avatars return 404.)
        return False

  user['profile_image_url_https_orig'] = user['profile_image_url_https']
  user['profile_image_url_https'] = local_filename
  return True


def process_tweets(trial_run, media_precount_global=None):
  image_count_global = 0
  video_count_global = 0
  media_count_global = 0

  # Loop 1: Go through all the months
  # ---------------------------------

  for date in index:
    try:
      year_str = '%04d' % date['year']
      month_str = '%02d' % date['month']
      data_filename = 'data/js/tweets/%s_%s.js' % (year_str, month_str)

      if not trial_run:
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
      month_tweet_count = 0
      month_media_count = 0
      directory_name = 'data/js/tweets/%s_%s_media' % (year_str, month_str)

      for tweet in data:
        month_tweet_count = month_tweet_count + 1
        retweeted = 'retweeted_status' in tweet.keys()

        # Before downloading any images, download an avatar for tweet's author
        # (same for retweet if asked to)
        if not trial_run and not args.skip_avatars:
          data_changed = download_avatar(tweet['user'])

          data_changed_retweet = False
          if not args.skip_retweets and retweeted:
            data_changed_retweet = download_avatar(tweet['retweeted_status']['user'])

          # Re-save the JSON file if we grabbed any avatars
          if data_changed or data_changed_retweet:
            resave_data(data, data_filename, first_data_line, year_str, month_str)

        # Don't continue with saving images if a retweet (unless forced to)
        if (args.skip_retweets) and retweeted:
          continue

        if tweet['entities']['media']:
          tweet_media_count = 1

          # Rewrite tweet date to be used in the filename prefix
          # (only first 19 characters + replace colons with dots)
          date = re.sub(r':', '.', tweet['created_at'][:19])


          # Loop 3: Go through all the media in a tweet
          # -------------------------------------------

          for media in tweet['entities']['media']:
            # media_url_orig being present means we already processed/downloaded
            # this image or video
            if 'media_url_orig' in media.keys() and not args.force_download:
              continue

            if args.force_download and 'media_url_orig' in media.keys():
              media['media_url'] = media['media_url_orig']

            # Only make the directory when we're ready to write the first file;
            # this will avoid empty directories
            if not trial_run and not os.path.isdir(directory_name):
              os.mkdir(directory_name)

            is_video = False
            # Video
            if '/video/' in media['expanded_url']:
              is_video = True
              url = media['expanded_url']
              local_filename = 'data/js/tweets/%s_%s_media/%s-%s-video-%s%s.mp4' %\
                  (year_str, month_str, date, tweet['id'], 'rt-' if retweeted else '',
                   tweet_media_count)
            # Animated GIF transcoded into a video
            elif 'tweet_video_thumb' in media['media_url']:
              is_video = True
              id = re.match(r'(.*)tweet_video_thumb/(.*)\.', media['media_url']).group(2)
              url = "https://video.twimg.com/tweet_video/%s.mp4" % id
              local_filename = 'data/js/tweets/%s_%s_media/%s-%s-gif-video-%s%s.mp4' %\
                  (year_str, month_str, date, tweet['id'], 'rt-' if retweeted else '',
                   tweet_media_count)
            # Regular non-animated image
            else:
              is_video = False
              url = media['media_url_https']
              extension = os.path.splitext(url)[1]
              # Download the original/best image size, rather than the default one
              url = url + ':orig'
              local_filename = 'data/js/tweets/%s_%s_media/%s-%s-%s%s%s' % \
                  (year_str, month_str, date, tweet['id'], 'rt-' if retweeted else '',
                   tweet_media_count, extension)

            can_be_copied = False
            downloaded = False
            download_tries = 3

            # If using an earlier archive as a starting point, try to find the desired
            # image file there first, and copy it if present
            if args.EARLIER_ARCHIVE_PATH and os.path.isfile(earlier_archive_path + local_filename):
              can_be_copied = True

            if not trial_run:
              sys.stdout.write("\r[%0.1f%%] %s/%s: %s %s %s..." %
                  (media_count_global / media_precount_global * 100, year_str, month_str, \
                  "Copying" if can_be_copied else "Downloading", \
                  "video" if is_video else "image", url.split('/')[-1]))
              sys.stdout.write("\033[K") # Clear the end of the line
              sys.stdout.flush()

              if can_be_copied:
                copyfile(earlier_archive_path + local_filename, local_filename)
              else:
                while not downloaded:
                  # Actually download the file!
                  if (is_video and download_video(url, local_filename)) or \
                     (not is_video and download_image(url, local_filename)):
                    downloaded = True
                  else:
                    download_tries = download_tries - 1
                    if download_tries == 0:
                      print("")
                      print("Failed to download %s after 3 tries." % url)
                      print("Please try again later?")
                      # Output debugging info if needed
                      if args.verbose:
                        print("Debug info: Tweet ID = %s " % tweet['id'])
                      sys.exit(-2)
                    time.sleep(5) # Wait 5 seconds before retrying

              # Change the URL so that the archive's index.html will now point to the
              # just-download local file...
              if (not is_video and download_images) or (is_video and download_videos):
                media['media_url_orig'] = media['media_url']
                media['media_url'] = local_filename

                # Re-save the original JSON file every time, so that the script can continue
                # from this point
                resave_data(data, data_filename, first_data_line, year_str, month_str)

            tweet_media_count = tweet_media_count + 1
            month_media_count = month_media_count + 1
            if is_video:
              video_count_global = video_count_global + 1
            else:
              image_count_global = image_count_global + 1
            media_count_global = media_count_global + 1

          # End loop 3 (images in a tweet)

      # End loop 2 (tweets in a month)
      if not trial_run and month_media_count:
        sys.stdout.write("\r%i images/videos downloaded from %s/%s." % (month_media_count, year_str, month_str))
        sys.stdout.write("\033[K") # Clear the end of the line
        sys.stdout.flush()
        print("")

    # Nicer support for Ctrl-C
    except KeyboardInterrupt:
      print("")
      print("Interrupted! Come back any time.")
      sys.exit(-3)

  # End loop 1 (all the months)
  return image_count_global, video_count_global, media_count_global


# Main entry point
# ---------------------------------

# Introduce yourself

print("Twitter export image fill 1.07")
print("by Marcin Wichary (aresluna.org) and others")
print("use --help to see options")
print("")

# Process arguments

args = parse_arguments()

download_images = not args.skip_images
download_videos, youtube_dl_path = find_youtube_dl()

# Check whether the earlier archive actually exists
# (This is important because failure would mean quietly downloading all the files again)

if args.EARLIER_ARCHIVE_PATH:
  earlier_archive_path = args.EARLIER_ARCHIVE_PATH
  # Normalizes the slash at the end so it supports both including and not including it
  earlier_archive_path = earlier_archive_path.rstrip('/') + '/'
  if not os.path.isfile(earlier_archive_path + '/data/js/tweet_index.js'):
    print("Could not find the earlier archive!")
    print("Make sure you're pointing at the directory that contains the index.html file.")
    sys.exit(-1)

# Prepare environment, etc.

if not os.path.isdir("img/avatars"):
  os.mkdir("img/avatars")

# Process the index file to see what needs to be done

index = load_tweet_index()

# Scan the file to know how much work needs to be done

print("Scanning...")
image_precount_global, video_precount_global, media_precount_global = process_tweets(True)

print("")
if not args.skip_images and not args.skip_videos:
  print("To process: %i months' worth of tweets with %i images and %i videos." % (len(index), image_precount_global, video_precount_global))
elif not args.skip_images:
  print("To process: %i months' worth of tweets with %i images." % (len(index), image_precount_global))
elif not args.skip_videos:
  print("To process: %i months' worth of tweets with %i videos." % (len(index), video_precount_global))
print("(You can cancel any time. Next time you run, the script should resume at the last point.)")
print("")

# Actually download everything

image_count_global, video_count_global, media_count_global = process_tweets(False, media_precount_global)

# Communicate success

print("")
print("Done!")
if download_images:
  print("%i images downloaded in total." % image_count_global)
if download_videos:
  print("%i videos downloaded in total." % video_count_global)
print("")

if video_count_global and not download_videos:
  print("%i videos have NOT been downloaded." % video_count_global)
  print("If you want, use the include-videos option to download videos.")
  print("For more info, use --help, or look at https://github.com/mwichary/twitter-export-image-fill")

  print("")
