# twitter-export-image-fill

Twitter allows you to download your tweet archive, but that archive doesn’t contain your images. Ergo, it is not really an archive.

This script:
- downloads all the images from your tweets locally
- rewrites the archive files so that they point to the local images

### Instructions

1. Request your Twitter archive from https://twitter.com/settings/account.
2. Wait for the email.
3. Download the archive from the email.
4. Unpack it somewhere.
5. Go to the root directory of that archive and run `twitter-export-image-fill.py` there.

Note: You can interrupt the script at any time and run it again – it should start where it left off.

### Details

- The script downloads the images in highest quality.
- Images from retweets are not downloaded.
- The original versions of modified JSON files are saved for reference.

### License

This script is in public domain. Run free.
