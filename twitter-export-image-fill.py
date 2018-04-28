#!/usr/bin/env python

'''
Twitter export image fill 1.10
by Marcin Wichary (aresluna.org)

Site: https://github.com/mwichary/twitter-export-image-fill

This is free and unencumbered software released into the public domain.
Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means. For more information, please refer to <http://unlicense.org/>
'''

# Imports
# ---------------------------------

import argparse
import json
import os
import re
import sys
import time
from shutil import copyfile
# The location of urlretrieve changed modules in Python 3
if (sys.version_info > (3, 0)):
  from urllib.request import urlretrieve
else:
  from urllib import urlretrieve


def print_intro():
  print("Twitter export image fill 1.10")
  print("by Marcin Wichary (aresluna.org) and others")
  print("use --help to see options")
  print("")


def parse_arguments():
  parser = argparse.ArgumentParser(description = 'Downloads all the images to your Twitter archive .')
  parser.add_argument('--include-videos', dest='PATH_TO_YOUTUBE_DL',
      help = 'use youtube_dl to download videos (and animated GIFs) in addition to images')
  parser.add_argument('--continue-after-failure', action='store_true',
      help = 'continue the process when one of the downloads fail (creates incomplete archive)')
  parser.add_argument('--backfill-from', dest='EARLIER_ARCHIVE_PATH',
      help = 'copy images downloaded into an earlier archive instead of downloading them again (useful for incremental backups)')
  parser.add_argument('--skip-retweets', action='store_true',
      help = 'do not download images or videos from retweets')
  parser.add_argument('--skip-images', action='store_true',
      help = 'do not download images in general')
  parser.add_argument('--skip-videos', action='store_true',
      help = 'do not download videos (and animated GIFs) in general')
  parser.add_argument('--skip-avatars', action='store_true',
      help = 'do not download avatar images')
  parser.add_argument('--verbose', action='store_true',
      help = 'show additional debugging info')
  parser.add_argument('--force-redownload', action='store_true',
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


def test_earlier_archive_path():
  if args.EARLIER_ARCHIVE_PATH:
    earlier_archive_path = args.EARLIER_ARCHIVE_PATH
    # Normalizes the slash at the end so it supports both including and not including it
    earlier_archive_path = earlier_archive_path.rstrip('/') + '/'
    if not os.path.isfile(earlier_archive_path + '/data/js/tweet_index.js'):
      print("Could not find the earlier archive!")
      print("Make sure you're pointing at the directory that contains the index.html file.")
      sys.exit(-1)
    return earlier_archive_path
  else:
    return None


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


def make_directory_if_needed(directory_path):
  if not os.path.isdir(directory_path):
    os.mkdir(directory_path)


def is_retweet(tweet):
  return 'retweeted_status' in tweet.keys()


def output_line(line):
  sys.stdout.write("\r%s\033[K" % line) # Clears the end of the line
  sys.stdout.flush()


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
def download_or_copy_avatar(user, total_image_count, total_video_count, total_media_precount, year_str, month_str):
  # _orig existing means we already processed this user
  if 'profile_image_url_https_orig' in user:
    return False

  avatar_url = user['profile_image_url_https']
  extension = os.path.splitext(avatar_url)[1]
  local_filename = "img/avatars/%s%s" % (user['screen_name'], extension)

  if not os.path.isfile(local_filename):
    can_be_copied = args.EARLIER_ARCHIVE_PATH and os.path.isfile(earlier_archive_path + local_filename)

    output_line("[%0.1f%%] %s/%s: %s avatar..." %
      ((total_image_count + total_video_count) / total_media_precount * 100, \
      year_str, month_str, \
      "Copying" if can_be_copied else "Downloading"))

    # If using an earlier archive as a starting point, try to see if the
    # avatar image is there and can be copied
    if can_be_copied:
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


def download_file(url, local_filename, is_video):
  downloaded = False
  download_tries = 3
  while not downloaded:
    if (is_video and download_video(url, local_filename)) or \
       (not is_video and download_image(url, local_filename)):
      return True
    else:
      download_tries = download_tries - 1
      if download_tries == 0:
        if not args.continue_after_failure:
          print("")
          print("")
          print("Failed to download %s after 3 tries." % url)
          print("Please try again later?")
          print("(Alternatively, use --continue-after-failure option to skip past failed files.)")
          # Output debugging info if needed
          if args.verbose:
            print("Debug info: Tweet ID = %s " % tweet['id'])
          sys.exit(-2)
        else:
          failed_files.append(url)
          return False
      time.sleep(3) # Wait 3 seconds before retrying
      sys.stdout.write(".")
      sys.stdout.flush()


def determine_image_or_video(medium, year_str, month_str, date, tweet, tweet_media_count):
  # Video
  if '/video/' in medium['expanded_url']:
    is_video = True
    separator = '-video'
    url = medium['expanded_url']
    extension = '.mp4'
  # Animated GIF transcoded into a video
  elif 'tweet_video_thumb' in medium['media_url']:
    is_video = True
    separator = '-gif-video'
    id = re.match(r'(.*)tweet_video_thumb/(.*)\.', medium['media_url']).group(2)
    url = "https://video.twimg.com/tweet_video/%s.mp4" % id
    extension = os.path.splitext(url)[1]
  # Regular non-animated image
  else:
    is_video = False
    separator = ''
    url = medium['media_url_https']
    extension = os.path.splitext(url)[1]
    # Download the original/best image size, rather than the default one
    url = url + ':orig'

  local_filename = 'data/js/tweets/%s_%s_media/%s-%s%s-%s%s%s' % \
      (year_str, month_str, date, tweet['id'], separator,
      'rt-' if is_retweet(tweet) else '', tweet_media_count, extension)

  return is_video, url, local_filename


def process_tweets(tweets_by_month, trial_run, total_media_precount=None):
  total_image_count = 0
  total_video_count = 0

  # Loop 1: Go through all the months
  # ---------------------------------

  for date in tweets_by_month:
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
      month_media_count = 0
      directory_name = 'data/js/tweets/%s_%s_media' % (year_str, month_str)

      for tweet in data:
        # Output the string just for the sake of status continuity
        if not trial_run:
          output_line("[%0.1f%%] %s/%s: Analyzing avatars..." %
              ((total_image_count + total_video_count) / total_media_precount * 100, year_str, month_str))

        # Before downloading any images, download an avatar for tweet's author
        # (same for retweet if asked to)
        if not trial_run and not args.skip_avatars:
          data_changed = download_or_copy_avatar(tweet['user'], \
              total_image_count, total_video_count, total_media_precount, year_str, month_str)

          data_changed_retweet = False
          if not args.skip_retweets and is_retweet(tweet):
            data_changed_retweet = download_or_copy_avatar(tweet['retweeted_status']['user'], \
                total_image_count, total_video_count, total_media_precount, year_str, month_str)

          # Re-save the JSON file if we grabbed any avatars
          if data_changed or data_changed_retweet:
            resave_data(data, data_filename, first_data_line, year_str, month_str)

        # Don't continue with saving images if a retweet (unless forced to)
        if (args.skip_retweets) and is_retweet(tweet):
          continue

        media = tweet['retweeted_status']['entities']['media'] if is_retweet(tweet) \
          else tweet['entities']['media']

        if media:
          tweet_media_count = 1

          # Rewrite tweet date to be used in the filename prefix
          # (only first 19 characters + replace colons with dots)
          date = re.sub(r':', '.', tweet['created_at'][:19])


          # Loop 3: Go through all the media in a tweet
          # -------------------------------------------

          for medium in media:
            # media_url_orig being present means we already processed/downloaded
            # this image or video
            if 'media_url_orig' in medium.keys() and not args.force_redownload:
              continue

            # If forcing download, the above has to be undone.
            if args.force_redownload and 'media_url_orig' in medium.keys():
              medium['media_url'] = medium['media_url_orig']

            is_video, url, local_filename = \
                determine_image_or_video(medium, year_str, month_str, date, tweet, tweet_media_count)

            if not trial_run:
              # If using an earlier archive as a starting point, try to find the desired
              # image file there first, and copy it if present
              can_be_copied = args.EARLIER_ARCHIVE_PATH and os.path.isfile(earlier_archive_path + local_filename)

              output_line("[%0.1f%%] %s/%s: %s %s %s..." %
                  ((total_image_count + total_video_count) / total_media_precount * 100, \
                  year_str, month_str, \
                  "Copying" if can_be_copied else "Downloading", \
                  "video" if is_video else "image", url.split('/')[-1]))

              # Only make the directory when we're ready to write the first file;
              # this will avoid empty directories
              make_directory_if_needed(directory_name)

              success = False
              if can_be_copied:
                copyfile(earlier_archive_path + local_filename, local_filename)
                success = True
              else:
                success = download_file(url, local_filename, is_video)

              # Change the URL so that the archive's index.html will now point to the
              # just-downloaded local file...
              if success and ((not is_video and download_images) or (is_video and download_videos)):
                medium['media_url_orig'] = medium['media_url']
                medium['media_url'] = local_filename

                # Re-save the original JSON file every time, so that the script can continue
                # from this point
                resave_data(data, data_filename, first_data_line, year_str, month_str)

            tweet_media_count += 1
            month_media_count += 1

            if is_video:
              total_video_count += 1
            else:
              total_image_count += 1

          # End loop 3 (images in a tweet)

      # End loop 2 (tweets in a month)
      if not trial_run and month_media_count:
        output_line("%i images/videos downloaded from %s/%s." % (month_media_count, year_str, month_str))
        print("")

    # Nicer support for Ctrl-C
    except KeyboardInterrupt:
      print("")
      print("Interrupted! Come back any time.")
      sys.exit(-3)

  # End loop 1 (all the months)
  return total_image_count, total_video_count


# Main entry point
# ---------------------------------

print_intro()

# Process arguments, find components

args = parse_arguments()
download_images = not args.skip_images
download_videos, youtube_dl_path = find_youtube_dl()

# Check whether the earlier archive actually exists
# (This is important because failure would mean quietly downloading all the files again)

earlier_archive_path = test_earlier_archive_path()

# Prepare environment, etc.

if not args.skip_avatars:
  make_directory_if_needed("img/avatars")
if args.continue_after_failure:
  failed_files = []

# Process the index file

tweets_by_month = load_tweet_index()
month_count = len(tweets_by_month)

# Scan the file to know how much work needs to be done

print("Scanning...")
total_image_precount, total_video_precount = \
    process_tweets(tweets_by_month, True)
total_media_precount = total_image_precount + total_video_precount

print("")
if not args.skip_images and not args.skip_videos:
  print("To process: %i months' worth of tweets with %i images and %i videos." % \
      (month_count, total_image_precount, total_video_precount))
elif not args.skip_images:
  print("To process: %i months' worth of tweets with %i images." % \
      (month_count, total_image_precount))
elif not args.skip_videos:
  print("To process: %i months' worth of tweets with %i videos." % \
      (month_count, total_video_precount))
print("(You can cancel any time. Next time you run, the script should resume at the last point.)")
print("")

# Actually download everything

total_image_count, total_video_count = \
    process_tweets(tweets_by_month, False, total_media_precount)

# Communicate success

print("")
print("Done!")
if download_images:
  print("%i images downloaded in total." % total_image_count)
if download_videos:
  print("%i videos downloaded in total." % total_video_count)
print("")

if len(failed_files):
  print("%i files have **NOT** been downloaded. Here are the URLs:" % len(failed_files))
  for line in failed_files:
    print(line)
  print("")

if total_video_count and not download_videos:
  print("%i videos have **NOT** been downloaded." % total_video_count)
  print("If you want, use the include-videos option to download videos.")
  print("For more info, use --help, or look at https://github.com/mwichary/twitter-export-image-fill")
  print("")
