"""
Set path attribute as this directory if running from source,
and as the data path if running from the packaged app.
"""
import os
path = os.path.realpath(
    os.path.dirname(__file__)
)
path = path.replace('library.zip', '')