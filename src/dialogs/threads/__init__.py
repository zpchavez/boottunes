"""
Code used by threads.

Copyright (C) 2010 Zachary Chavez
BootTunes is licensed under the GPLv2.
http://www.gnu.org/licenses/gpl-2.0.html
"""

class ReadLocker:
    """
    Context manager for QReadWriteLock::lockForRead()

    """
    def __init__(self, lock):
        self.lock = lock
    def __enter__(self):
        self.lock.lockForRead()
    def __exit__(self, type, value, tb):
        self.lock.unlock()

class WriteLocker:
    """
    Context manager for QReadWriteLock::lockForWrite()

    """
    def __init__(self, lock):
        self.lock = lock
    def __enter__(self):
        self.lock.lockForWrite()
    def __exit__(self, type, value, tb):
        self.lock.unlock()

