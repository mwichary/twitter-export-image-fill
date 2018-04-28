# twitter-export-image-fill

Twitter allows you to download your tweet archive, but that archive doesn’t contain your images or videos. Ergo, it is not really an archive.

This script:
- downloads all the images and videos from your tweets locally
- rewrites the archive files so that they point to the local images/videos

(I wrote a [similar script for a Medium archive](https://github.com/mwichary/medium-export-image-fill).)


### Why you should have a complete archive of your own data

- n+1 backups is better than n backups.
- Your own backup will make it possible to get to your data if you’re offline, or if Twitter happens to be down.
- Someone can hack into your account and delete your tweets.
- *You* can accidentally delete your tweets or images.
- Someone at Twitter can make a mistake and delete them, too.
- Years or decades from now, Twitter might cease to exist.


### Instructions

1. Request your Twitter archive from the bottom of https://twitter.com/settings/account.
2. Wait for the email.
3. Download the archive from the email.
4. Unpack it somewhere.
5. Go to the root directory of that archive and run `twitter-export-image-fill.py` there (using terminal/command line).

Note: You can interrupt the script at any time and run it again – it should start where it left off.

<img width="1154" src="https://cloud.githubusercontent.com/assets/2061609/21486338/edb3daf4-cb67-11e6-88ca-928b1b017b10.png">


### Options

`--include-videos PATH_TO_YOUTUBE_DL`

Download videos and animated GIFs from tweets. You have to
<a href='https://rg3.github.io/youtube-dl/download.html'>download/install
youtube-dl</a> and then provide a path to it, e.g.
`--include-videos /usr/local/Cellar/youtube-dl/2017.01.05/bin/youtube-dl`
The script will try to find youtube-dl in its common path, but it might fail.

Note: This includes animated GIFs, which Twitter transcodes into videos.

`--continue-after-failure`

Continue the process when one of the downloads fail. This will create an incomplete archive,
although it is sometimes necessary as apparently Twitter deletes some images.
The list of failed images will be output at the end.

`--backfill-from EARLIER_ARCHIVE_PATH`

Use an earlier archive to get images from if possible, instead of downloading (useful for incremental backups), e.g. `--backfill-from ~/Desktop/tweet-archive`

`--skip-retweets`

Do not download images from retweets (done by default).

`--skip-images`

Do not download any images (just videos).

`--skip-videos`

Do not download any videos (just images).

`--skip-avatars`

Do not download avatars from tweets (by default, user avatars are downloaded alongside tweet images).

`--force-redownload`

Force the script to not be very smart and download again stuff that’s already been download.


### Details

- The script downloads the images in highest quality.
- The original versions of modified JSON files are saved for reference.
- Images are downloaded into `data/js/tweets/YYYY_MM_media` subdirectories.
- User avatars are downloaded into `img/avatars` directory.


### FAQ

**Does this work on Windows or Linux?**

I wrote/tested it on Mac OS only, but I’ve heard of people having success
running it on Windows. Others reported it worked for them properly on
Ubuntu, FreeBSD, and Debian.

**Does this download videos in addition to images?**

Sort of. There is an experimental youtube-dl integration. Check out the
`include-videos` parameter above. Note that the videos won’t be playable
from the archive’s local webpage, but they will be downloaded locally
into your file system.

**Some of my images fail to load, even though they open on Twitter**

Image URLs can change if you protect (or unprotect?) your account, and the
archive can get out of sync. If that matches your usage, simply
re-download a fresh archive.


### License

This script is in public domain. Run free.


### Version history

**1.10 (28 Apr 2018)**
- Better downloading of retweets
- Added an option to allow to skip broken images
- Tons of internal code clean-up (thanks to <a href='https://github.com/keithrbennett'>@keithrbennett</a>)

**1.06 (28 Apr 2018)**
- Better communication of progress

**1.05 (27 Apr 2018)**
- Better integration with youtube-dl for downloading videos and animated GIFs
- Semi-automatic detection of youtube-dl
- Downloading videos will now resume correctly after stopping
- Images and videos and retweets are now downloaded by default (but you can opt out)

**1.04 (26 Apr 2018)**
- Downloads animated GIFs as videos rather than stills (thanks to AlexLady for inspiration)

**1.03 (5 Jan 2017)**
- Downloads videos through youtube-dl “integration” (thanks to Nelson Minar and Benjamin Zanin for inspiration)
- Downloads avatar images, too (code submitted by <a href='https://github.com/edsu'>@edsu</a>)
- Should work on Python 2 and 3 (code submitted by <a href='https://github.com/glasnt'>@glasnt</a>)

**1.02 (27 Dec 2016)**
- Fixed the first line to allow it to run on more systems (thanks to Ariel Millennium Thornton)

**1.01 (27 Dec 2016)**
- Added an option to start from an earlier archive
- Added an option to include images in retweets
- Small UI fixes

**1.00 (26 Dec 2016)**
- Initial release
