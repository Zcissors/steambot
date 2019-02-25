#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Metaclass for any class to make it produce singleton instances only.

This is thread-safe, but acquiring locks for initialization will block the event loop for a minute
period of time, so cache the result to the call if it becomes an issue in the future.
"""
import collections
import threading


_instances = {}
_locks_lock = threading.Lock()
_locks = collections.defaultdict(threading.Lock)


class SingletonMeta(type):
    def __call__(cls, *args, **kwargs):
        with _locks_lock:
            lock = _locks[cls]

        with lock:
            if cls not in _instances:
                instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
                _instances[cls] = instance
            else:
                instance = _instances[cls]

            return instance
