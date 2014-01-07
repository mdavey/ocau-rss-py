ocau-rss-py
===========

Python script to generate static RSS feeds of OCAU's forsale forums

Setup
=====

    pip install -r requirements.txt
    python storage.py setup

Update LOGIN_DETAILS, RSS_DIRECTORY in monitor.py

 * RSS_DIRECTORY is the location to save the RSS files
 * LOGIN_DETAILS is the filename that contains your OCAU username and password in the format: `username#password`

To run the script:

    python monitor.py

