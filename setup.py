#!/usr/bin/env python
import sys
from io import open
from os import walk
from os.path import join, relpath

from setuptools import setup

import setuptools

requires = [x.strip() for x in open("requirements.txt")]

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='botfriend',
    version='0.7.0',
    author='Leonard Richardson',
    author_email='leonardr@segfault.org',
    url="https://github.com/leonardr/botfriend/",
    description="A server-side framework that makes it easy to manage artistic bots that post to social media.",
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'botfriend.backlog.clear = botfriend.scripts:BacklogClearScript.run',
            'botfriend.backlog.load = botfriend.scripts:BacklogLoadScript.run',
            'botfriend.backlog.show = botfriend.scripts:BacklogShowScript.run',
            'botfriend.bots = botfriend.scripts:BotListScript.run',
            'botfriend.dashboard = botfriend.scripts:DashboardScript.run',
            'botfriend.post = botfriend.scripts:PostScript.run',
            'botfriend.republish = botfriend.scripts:RepublicationScript.run',
            'botfriend.schedule.clear = botfriend.scripts:ScheduledPostsClearScript.run',
            'botfriend.schedule.load = botfriend.scripts:ScheduledPostsLoadScript.run',
            'botfriend.schedule.show = botfriend.scripts:ScheduledPostsShowScript.run',
            'botfriend.state.clear = botfriend.scripts:StateClearScript.run',
            'botfriend.state.refresh = botfriend.scripts:StateRefreshScript.run',
            'botfriend.state.set = botfriend.scripts:StateSetScript.run',
            'botfriend.state.show = botfriend.scripts:StateShowScript.run',
            'botfriend.test.publisher = botfriend.scripts:PublisherTestScript.run',
            'botfriend.test.stress = botfriend.scripts:StressTestScript.run',
        ]
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Text Processing',
        'Topic :: Artistic Software',
    ],
)
