.. This file is a part of the AnyBlok project
..
..    Copyright (C) 2021 Franck Bret <franckbret@gmail.com>
..
.. This Source Code Form is subject to the terms of the Mozilla Public License,
.. v. 2.0. If a copy of the MPL was not distributed with this file,You can
.. obtain one at http://mozilla.org/MPL/2.0/.

.. image:: https://img.shields.io/pypi/pyversions/anyblok_media.svg?longCache=True
    :alt: Python versions

.. image:: https://travis-ci.org/AnyBlok/anyblok_media.svg?branch=master
    :target: https://travis-ci.org/AnyBlok/anyblok_media
    :alt: Build status

.. image:: https://coveralls.io/repos/github/AnyBlok/anyblok_media/badge.svg?branch=master
    :target: https://coveralls.io/github/AnyBlok/anyblok_media?branch=master
    :alt: Coverage

.. image:: https://img.shields.io/pypi/v/anyblok_media.svg
   :target: https://pypi.python.org/pypi/anyblok_media/
   :alt: Version status

.. image:: https://readthedocs.org/projects/anyblok-media/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://anyblok-media.readthedocs.io/en/latest/


===============
Anyblok Media
===============

This module provides AnyBlok bloks to manage a library of media, with tranform and tagging abilities. It also offers different storage stategies and is suitable for file upload.

Please note that this module use some jsonb columns, so it works only with a postgresql database.

+--------------------+-------------------+-------------------------------------------------+
| Blok               | Dependancies      | Description                                     |
+====================+===================+=================================================+
| **media**          |                   | Define base polymorphic Media class             |
+--------------------+-------------------+-------------------------------------------------+
| **media-image**    |                   | Media.Image class, suitable for image files     |
+--------------------+-------------------+-------------------------------------------------+
| **media-audio**    |                   | Media.Audio class, suitable for audio files     |
+--------------------+-------------------+-------------------------------------------------+
| **media-video**    |                   | Media.Video class suitable for video files      |
+--------------------+-------------------+-------------------------------------------------+

This module is released under the terms of the `Mozilla Public License`.

See the `latest documentation <http://doc.anyblok-media.anyblok.org>`_


Features
--------

* Create media from binary data (form / upload), from file path on disk or from remote url
* Store media file on database or disk
* Manage metadata within image, audio and video files
* Ability to generate several versions from a media source file (image only for now) and transformation rules

Example
-------

You must at least define in you configuration file the following path on your disk : 

* source_path_prefix (a path used to store original source files)
* media_path_prefix (a path used to store the tranformed files)

Not mandatory configuration entry:

* source_path_tmp (a path for tmp files, mainly used when uploading multipart files)

In your project model file, add a class that inherit from Media.Image, Media.Audio or Media.Video according to your needs.

mymodels.py

```
from anyblok import Declarations


register = Declarations.register
Model = Declarations.Model


@register(Model.Media)
class Image:
    SOURCE_STORAGE_STRATEGY = "disk"
    SOURCE_DISK_STORAGE_PATTERN = "{source_path_prefix}/image/{year}/{month}/{day}/{filename}.{extension}"
    DESTINATION_PATH_PATTERN = "{media_path_prefix}/image/{year}/{month}/{day}/{filename}-{name}.{extension}"
    URL_PATTERN = (
        "/media/image/{year}/{month}/{day}/{filename}-{name}.{extension}"
    )
    PROCESS_PARAMS = {
        "wide": {
            "size": "1200x800",
            "width": 1200,
            "height": 800,
            "extension": "jpg",
            "file_format": "JPEG",
            "transformation_mode": "resize",
        },
        "large": {
            "size": "600x400",
            "width": 600,
            "height": 400,
            "extension": "jpg",
            "file_format": "JPEG",
            "transformation_mode": "resize",
        },
        "medium": {
            "size": "300x200",
            "width": 300,
            "height": 200,
            "extension": "jpg",
            "file_format": "JPEG",
            "transformation_mode": "resize",
        },
        "square-small": {
            "size": "160x160",
            "width": 160,
            "height": 160,
            "extension": "jpg",
            "file_format": "JPEG",
            "transformation_mode": "crop",
        },
        "small": {
            "size": "160x120",
            "width": 160,
            "height": 120,
            "extension": "jpg",
            "file_format": "JPEG",
            "transformation_mode": "preserve",
        },
    }


@register(Model.Media)
class Audio:
    SOURCE_STORAGE_STRATEGY = "disk"
    SOURCE_DISK_STORAGE_PATTERN = "{source_path_prefix}/audio/{year}/{month}/{day}/{filename}.{extension}"
    DESTINATION_PATH_PATTERN = (
        "{media_path_prefix}/audio/{filename}-{name}.{extension}"
    )
    URL_PATTERN = "/media/audio/{filename}-{name}.{extension}"


@register(Model.Media)
class Video:
    SOURCE_STORAGE_STRATEGY = "disk"
    SOURCE_DISK_STORAGE_PATTERN = "{source_path_prefix}/video/{year}/{month}/{day}/{filename}.{extension}"
    DESTINATION_PATH_PATTERN = (
        "{media_path_prefix}/video/{filename}-{name}.{extension}"
    )
    URL_PATTERN = "/media/video/{filename}-{name}.{extension}"
```

Author
------

Franck Bret
https://github.com/franckbret

Contributors
------------

...

Credits
-------

...

.. _`anyblok_media`: https://github.com/AnyBlok/anyblok_media
