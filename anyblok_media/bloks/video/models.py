# This file is a part of the AnyBlok / Media project
#
#    Copyright (C) 2021 Franck Bret <franckbret@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Media model
"""
import io
import os
from datetime import datetime, date
from logging import getLogger

from mediafile import MediaFile

from anyblok import Declarations
from anyblok.config import Configuration

logger = getLogger(__name__)

register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin


@register(Model)
class Media:
    @classmethod
    def get_media_types(cls):
        res = super(Media, cls).get_media_types()
        res.update(dict(video="Video"))
        return res


@register(Model)
class Tag:
    @classmethod
    def get_media_types(cls):
        res = super(Tag, cls).get_media_types()
        res.update(dict(video="Video"))
        return res

@register(Model.Media, tablename=Model.Media)
class Video(Model.Media):
    MEDIA_TYPE = "video"
    PROCESS_PARAMS = []
    DESTINATION_PATH_PATTERN = ""
    URL_PATTERN = ""
    WANTED = [
        "title",
        "author",
        "genres",
        "year",
        "country",
        "label",
        "comments",
    ]

    def process(self):
        if self.state != "published":
            self.state = "published"

    def grab_metadata_from_source(self):
        f = MediaFile(self.file_path)
        meta = dict()
        for field in self.WANTED:
            v = getattr(f, field)
            if v:
                if field == "genres":
                    if type(v) == str:
                        # cleanup genre string and convert to a list
                        v = [
                            t.strip().lower()
                            for t in filter(None, v.split(","))
                        ]
                    elif type(v) == list:
                        res = []
                        for item in v:
                            for elt in filter(None, item.split(",")):
                                res.append(elt.strip().lower())
                        v = res
                meta[field] = v

        return meta

    def write_metadata_to_source(self):
        f = MediaFile(self.file_path)
        tag_list = [
            tag.name
            for tag in self.registry.Tag.query()
            .filter_by(media_type="video")
            .all()
        ]
        for field, v in self.meta.items():
            if field == "genres" and type(v) == list:
                genres_tags = []
                for tag in v:
                    if tag not in tag_list:
                        # Cleanup new tag
                        tag = tag.strip().lower()
                        if tag:
                            self.registry.Tag.insert(
                                name=tag, media_type="video"
                            )
                    genres_tags.append(tag)
                v = genres_tags
            setattr(f, field, v)
        f.save()

    @classmethod
    def before_update_orm_event(cls, mapper, connection, target):
        target.edit_date = datetime.now()
        if target.meta:
            target.write_metadata_to_source()

