#!/usr/bin/env python
import sys
from io import open
from os import walk
from os.path import join, relpath

from setuptools import setup

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

entry_points = {
    'scripts': [
        # botfriend/scripts/dashboard.py:main()
        'botfriend = botfriend.scripts.dashboard:main',
        'botfriend-backlog = botfriend.scripts.backlog:main',
        'botfriend-backlog-clear = botfriend.scripts.backlog_clear:main',
    ]
}
