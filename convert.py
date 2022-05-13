import os
import mammoth
from mammoth.cli import ImageWriter
import requests
import re
import datetime
import urllib.parse
from slugify import slugify

def main():
    # erase() # uncomment to erase existing content
    
    # open list of urls to convert
    with open('urls.txt', 'r') as f:
        for line in f:
            process(line.strip())

def erase():
    folders = ['images', 'markdown', 'docx']
    for folder in folders:
        for file in os.listdir(folder):
            os.remove(folder + '/' + file)

def process(url):
    url = url.replace('/edit', '/export?format=docx')

    # get document
    r = requests.get(url)
    
    # find the filename of the file downloaded by the request
    filename = urllib.parse.unquote(r.headers['Content-Disposition'].split('filename=')[1].split(';')[1].replace("filename*=UTF-8''", ''))

    # title is filename without extension
    title = filename.split('.')[0]

    # slug is the filename without the extension, slugified
    slug = slugify(filename.split('.')[0])

    # save the file to /docx folder
    with open('docx/' + filename, 'wb') as f:
        f.write(r.content)

    #  using mammoth, convert the docx to markdown
    with open('docx/' + filename, 'rb') as f:
        # process with mammoth
        result = mammoth.convert_to_markdown(f, convert_image=mammoth.images.img_element(ImageWriter('images')))

        # markdown is the result of the conversion
        md = result.value

        # remove all ids and classes from the markdown
        md = re.sub(r'\s+id="[^"]*"', '', md)
        md = re.sub(r'\s+class="[^"]*"', '', md)

        # remove any empty <a> tags
        md = re.sub(r'<a>\s*</a>', '', md)

        # remove any escaped periods
        md = re.sub(r'\\.', '.', md)

        # get todays date
        date = datetime.datetime.now().strftime("%Y-%m-%d")

        # first paragraph is the description of the article
        description = md.split('\n')[0]

        # remove description from markdown
        md = md.replace(description, '')

        # create frontmatter
        frontmatter = f"""
---
h1: "{title}"
title: "{title}"
date: "{date}"
description: {description}
---
        """

        # combine frontmatter and markdown
        md = frontmatter + '\n' + md

        # trim md
        md = md.strip()
        
        # find all images in the markdown
        images = re.findall(r'!\[.*\]\((.*)\)', md)

        # loop images
        for image in images:
            # new name is slug + image name
            new_name = slug + '-' + image
            # rename the file in images folder
            os.rename('images/' + image, 'images/' + new_name)

            # replace the image in the markdown with the new image name
            # change the base_url to wherever your images are stored
            base_url = '/images/'
            md = md.replace(image, base_url + new_name)

    # save the markdown to the /markdown folder
    with open('markdown/' + slug + '.md', 'w') as f:
        f.write(md)

if __name__ == '__main__':
    main()
