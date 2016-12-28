# twitter-export-image-fill

Twitter allows you to download your tweet archive, but that archive doesn’t contain your images. Ergo, it is not really an archive.

This script:
- downloads all the images from your tweets locally
- rewrites the archive files so that they point to the local images


### Instructions

1. Request your Twitter archive from the bottom of https://twitter.com/settings/account.
2. Wait for the email.
3. Download the archive from the email.
4. Unpack it somewhere.
5. Go to the root directory of that archive and run `twitter-export-image-fill.py` there (using terminal/command line).

Note: You can interrupt the script at any time and run it again – it should start where it left off.

<img width="1154" src="https://cloud.githubusercontent.com/assets/2061609/21486338/edb3daf4-cb67-11e6-88ca-928b1b017b10.png">


### Options

`--include-retweets` 

Download images from retweets (by default, the script only downloads images from your own tweets)

`--continue-from EARLIER_ARCHIVE_PATH`

Use an earlier archive to get images from if possible, instead of downloading (useful for incremental backups), e.g. `--continue-from ~/Desktop/tweet-archive`


### Details

- The script downloads the images in highest quality.
- The original versions of modified JSON files are saved for reference.


### FAQ

**Does this work on Windows?**

Not sure. I wrote/tested it on Mac OS only. If you run it on Windows (successfully or not), please let me know.

**Does this download videos in addition to images?**

Not sure. Probably not. Let me know if you know!


### License

This script is in public domain. Run free.


### Version history

**1.01 (Dec 2016)** 
- Added an option to start from an earlier archive 
- Added an option to include images in retweets
- Small UI fixes

**1.00 (Dec 2016)**
- Initial release
