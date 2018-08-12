#!/usr/bin/env python
import sys
from io import open
from os import walk
from os.path import join, relpath

from setuptools import setup

#!/usr/bin/env python
import sys
from io import open

import setuptools

requires = [
    'olipy',
    'sqlalchemy',
    'pyyaml',
    'nose',
    'tweepy',
    'TextBlob',
    'Mastodon.py',
    'requests',
    'beautifulsoup4',
    'feedparser',
    'pytumblr',
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='botfriend',
    version='0.5.0',
    author='Leonard Richardson',
    author_email='leonardr@segfault.org',
    url="https://github.com/leonardr/botfriend/",
    description="A server-side framework that makes it easy to manage artistic bots that post to social media.",
    license='GPLv3',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'botfriend.dashboard = botfriend.scripts:DashboardScript.run',
        ]
    },
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Text Processing',
        'Topic :: Artistic Software',
    ],
)
