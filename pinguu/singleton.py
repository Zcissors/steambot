#!/usr/bin/env python
# -*- coding: utf-8 -*-
import functools


class SingletonMeta(type):
    """
    Metaclass for a singleton class. Each instance of the class that is made will be
    the same object returned. This is lazily initialized.
    """

    @functools.lru_cache(maxsize=None, typed=True)
    def __call__(cls, *args, **kwargs):
        """Creates a new instance of the implementing class."""
        return super(SingletonMeta, cls).__call__(*args, **kwargs)
