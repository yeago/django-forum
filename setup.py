#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-shitty-forum',
    version="0.2",
    author='Steve Yeago',
    author_email='subsume@gmail.com',
    description='Forum in Django. Don\'t use it, it sucks.',
    url='http://github.com/subsume/django-forum',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development"
    ],
)
