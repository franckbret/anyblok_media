# This file is a part of the anyblok_media project
#
#    Copyright (C) 2021 Franck Bret <franckbret@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
# -*- coding: utf-8 -*-
"""Setup script for anyblok_media"""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'VERSION'),
          'r', encoding='utf-8') as version_file:
    version = version_file.read()

with open(os.path.join(here, 'README.rst'),
          'r', encoding='utf-8') as readme_file:
    readme = readme_file.read()

with open(os.path.join(here, 'CHANGELOG.rst'),
          'r', encoding='utf-8') as changelog_file:
    changelog = changelog_file.read()

requirements = [
    'anyblok',
    'anyblok_mixins',
    'Pillow',
    'mediafile',
    'pyexiv2',
    'python-slugify',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='anyblok_media',
    version=version,
    description="Media file management with transform and tagging abilities",
    long_description=readme + '\n\n' + changelog,
    author="Franck Bret",
    author_email='franckbret@gmail.com',
    url='http://docs.anyblok-media.anyblok.org/' + version,
    packages=find_packages(),
    entry_points={
        'bloks': [
            'media=anyblok_media.bloks.media:MediaBlok',
            'media-image=anyblok_media.bloks.image:MediaImageBlok',
            'media-audio=anyblok_media.bloks.audio:MediaAudioBlok',
            'media-video=anyblok_media.bloks.video:MediaVideoBlok',
        ],
    },
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='anyblok, media, image, audio, video, tag, metadata',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
