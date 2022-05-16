1. Install the dependencies: `pipenv install`
1. Make your Google Doc file accessible to anyone with the URL
1. Copy the share link from Docs to a new line on urls.txt
1. Make sure it ends with /edit and not /edit#
1. Run: `pipenv run python convert.py`

If you're not using pipenv, use requirements.txt instead.

You can also use one of the options below:

- `pipenv run python convert.py -r`: This will remove all existing files in the docx, images, and markdown folders.
- `pipenv run python convert.py -u example.txt`: Use a different filename for the list of urls instead of the default urls.txt.

This script is specific to my needs, but if you wanted to extend it to push content to WordPress, for example, you could probably do that pretty easily.