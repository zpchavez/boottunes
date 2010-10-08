"""
Set path attribute as this directory if running from source,
and as the data path if running from the packaged app.
"""
import os
#if 'library.zip' in __file__:
if True:
#    path = os.path.realpath(
#        os.path.dirname(__file__) + os.sep + '..'
#            + os.sep +  'data' + os.sep
#    )
    path = os.path.realpath(
        os.path.dirname(__file__)
    )
    path = path.replace('library.zip', '')
else:
    path = os.path.dirname(__file__)