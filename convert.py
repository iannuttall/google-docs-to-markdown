import sys
import os
import mammoth
from mammoth.cli import ImageWriter
import html2markdown
import requests
import re
import datetime
import urllib.parse
from slugify import slugify
from bs4 import BeautifulSoup as bs

def main(filename):
    # erase() # uncomment to erase existing content
    
    # open list of urls to convert
    with open(filename, 'r') as f:
        for line in f:
            process(line.strip())

def erase():
    folders = ['images', 'markdown', 'docx']
    for folder in folders:
        for file in os.listdir(folder):
            # if file is .gitkeep or .gitignore, skip it
            if file == '.gitkeep' or file == '.gitignore':
                continue
            os.remove(folder + '/' + file)

def process(url):
    # clean url
    url = url.replace(url.split('/')[-1], '') + 'export?format=docx'

    # get document
    r = requests.get(url)
    
    # find the filename of the file downloaded by the request
    filename = urllib.parse.unquote(r.headers['Content-Disposition'].split('filename=')[1].split(';')[1].replace("filename*=UTF-8''", ''))

    # title is filename without extension
    title = filename.split('.')[0].strip()

    # slug is the filename without the extension, slugified
    slug = slugify(filename.split('.')[0])

    # save the file to /docx folder
    with open('docx/' + filename, 'wb') as f:
        f.write(r.content)

    #  using mammoth, convert the docx to markdown
    with open('docx/' + filename, 'rb') as f:
        # process with mammoth
        result = mammoth.convert_to_html(f, convert_image=mammoth.images.img_element(ImageWriter('images')))

        # markdown is the result of the conversion
        # md = result.value
        md = html2markdown.convert(result.value)

        # remove all ids and classes from the markdown
        md = re.sub(r'\s+id="[^"]*"', '', md)
        md = re.sub(r'\s+class="[^"]*"', '', md)

        # remove any empty <a> tags
        md = re.sub(r'<a>\s*</a>', '', md)

        # remove any escaped periods
        md = re.sub(r'\\.', '.', md)

        # remove any &nbsp;
        md = re.sub(r'&nbsp;', '', md)

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
            base_url = '/static/img/blog/'
            md = md.replace(image, base_url + new_name)

        # find all tables in the markdown using soup
        soup = bs(md, 'html.parser')
        tables = soup.find_all('table')

        # loop tables
        for table in tables:
            # transform table
            md = md.replace(str(table), transform_table(table))

    # save the markdown to the /markdown folder
    with open('markdown/' + slug + '.md', 'w') as f:
        f.write(md)

def transform_table(table):
    # create empty tbody
    tbody = bs('', 'html.parser')

    # first row of table is the header
    header = table.tr.extract()

    # create thead using header
    thead = bs(f'<thead>{header}</thead>', 'html.parser')

    # loop through rows in table
    for row in table.find_all('tr'):
        tbody.append(row)

    # create tbody
    tbody = bs(f'<tbody>{tbody}</tbody>', 'html.parser')

    # convert tbody to string
    tbody = str(tbody)

    # replace th with td
    tbody = tbody.replace('<th>', '<td>')
    tbody = tbody.replace('</th>', '</td>')

    # create new table with thead and tbody
    new_table = bs(f'<table>{thead}{tbody}</table>', 'html.parser')

    # convert new table to string
    new_table = str(new_table)

    # remove <p> and </p>
    new_table = new_table.replace('<p>', '')
    new_table = new_table.replace('</p>', '')

    # remove all whitespace
    new_table = new_table.replace('\n', '')
    new_table = new_table.replace('\t', '')
    new_table = new_table.replace('\r', '')
    new_table = new_table.replace('\f', '')

    # convert new table back to soup object
    new_table = bs(new_table, 'html.parser')

    # add classes
    new_table.find('table').attrs['class'] = 'table is-bordered is-narrow is-fullwidth'

    # prettify new table
    new_table = new_table.prettify()

    # return table
    return f'<div class="table-expand">{new_table}</div>'

if __name__ == '__main__':
    # if -r is passed as an argument, run erase()
    if '-r' in sys.argv:
        erase()

    # default file is urls.txt
    file = 'urls.txt'

    # get -u to specify list of urls to convert
    if '-u' in sys.argv:
        file = sys.argv[sys.argv.index('-u') + 1]

    # if file does not exist, exit
    if not os.path.exists(file):
        print(f'List of urls does not exist. Make sure the {file} file is created first.')
        exit()

    main(file)
