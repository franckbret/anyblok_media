# This file is a part of the AnyBlok / Media project
#
#    Copyright (C) 2021 Franck Bret <franckbret@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Media model
"""
import os
import io
import random
from datetime import datetime
from uuid import uuid4
from urllib.request import urlopen
from logging import getLogger

import requests
from slugify import slugify

from anyblok.config import Configuration, ConfigurationException
from anyblok import Declarations
from anyblok.column import (
    LargeBinary,
    Integer,
    String,
    Selection,
    UUID,
)
from anyblok.relationship import Many2Many
from anyblok_postgres.column import Jsonb

logger = getLogger(__name__)

register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin


@register(Model, tablename="join_media_and_tag_for_tags")
class MediaTag:
    media_uuid = UUID(
        primary_key=True,
        default=uuid4,
        binary=False,
        nullable=False,
        unique=False,
        foreign_key="Model.Media=>uuid",
    )
    tag_uuid = UUID(
        primary_key=True,
        default=uuid4,
        binary=False,
        nullable=False,
        unique=False,
        foreign_key="Model.Tag=>uuid",
    )


@register(Model)
class Tag(Mixin.UuidColumn, Mixin.TrackModel):
    name = String(label="Tag name")
    media_type = Selection(selections="get_media_types", nullable=False)

    @classmethod
    def get_media_types(cls):
        return dict(
            media="Media",
        )


@register(Model)
class Media(Mixin.UuidColumn, Mixin.TrackModel, Mixin.WorkFlow):
    """Base polymorphic class for Model.Media
    Define a media object with an original source file storage strategy,
    metadata, transformation / conversion rules.

    Source file must be binary data.
    It can be provided through binary data directly (file upload) or via a
    remote url.

    The source file binary data can be stored on database or disk.
    """

    MEDIA_TYPE = None
    SOURCE_STORAGE_STRATEGIES = ["database", "disk"]
    SOURCE_STORAGE_STRATEGY = None

    media_type = Selection(selections="get_media_types", nullable=False)

    file = LargeBinary(label="Source file stored as binary")
    file_path = String(label="Source file stored on disk", size=256)
    file_url = String(label="Source file comes from remote url", size=256)

    filesize = Integer(label="Source file size (as bytes)")
    filename = String(label="Source file name", size=256)

    tags = Many2Many(label="Tags", model=Model.Tag, join_model=Model.MediaTag)

    meta = Jsonb(label="File metadata", default=dict())
    properties = Jsonb(label="File properties", default=dict())

    @classmethod
    def get_source_storage_strategy(cls):
        """Define a storage strategy for original source file."""
        if not cls.SOURCE_STORAGE_STRATEGY:
            logger.warning(
                "You should set SOURCE_STORAGE_STRATEGY to use that method"
            )
            return
        elif cls.SOURCE_STORAGE_STRATEGY not in cls.SOURCE_STORAGE_STRATEGIES:
            logger.warning(
                "SOURCE_STORAGE_STRATEGY not in SOURCE_STORAGE_STRATEGIES : %r"
                % cls.SOURCE_STORAGE_STRATEGIES
            )
            return
        else:
            return cls.SOURCE_STORAGE_STRATEGY

    @classmethod
    def get_workflow_definition(cls):
        """Define a default set of state workflow.
        Note that it is only state, no transition rules.
        """
        return {
            "draft": {
                "default": True,
                "allowed_to": ["published", "archived"],
            },
            "published": {
                "allowed_to": ["draft", "archived"],
            },
            "archived": {},
        }

    @classmethod
    def define_mapper_args(cls):
        """Mapper args for polymorphic identity"""
        mapper_args = super(Media, cls).define_mapper_args()
        if cls.__registry_name__ == "Model.Media":
            mapper_args.update({"polymorphic_on": cls.media_type})

        mapper_args.update({"polymorphic_identity": cls.MEDIA_TYPE})
        return mapper_args

    @classmethod
    def query(cls, *args, **kwargs):
        """Ensure default query on polymorphic models return records of the
        wanted media_type"""
        query = super(Media, cls).query(*args, **kwargs)
        if cls.__registry_name__.startswith("Model.Media."):
            query = query.filter(cls.media_type == cls.MEDIA_TYPE)
        return query

    @classmethod
    def get_media_types(cls):
        return dict(
            media="Media",
        )

    @classmethod
    def slugify_filename(cls, filename, random_suffix=False):
        """Given a filename, return a clean and unique one"""
        filename_split = filename.lower().split(".")
        extension = filename_split.pop()
        name = "".join(filename_split)
        if random_suffix:
            return "%s-%s.%s" % (
                slugify(name),
                random.randint(1e5, 1e6 - 1),
                extension,
            )
        else:
            return "%s.%s" % (
                slugify(name),
                extension,
            )

    @classmethod
    def get_file_metadata(cls, stream):
        """Given a file stream, reads its metadata"""
        raise NotImplementedError(
            "You must implement a method to read file metadata on your"
            " polymorphic class"
        )

    @classmethod
    def set_file_metadata(cls, stream):
        """Given a file stream, set its metadata"""
        raise NotImplementedError(
            "You must implement a method to set file metadata on your"
            " polymorphic class"
        )

    @classmethod
    def create(cls, **kwargs):
        """A method to create a new media file.
        To get benefits of this blok library you should always use create
        instead of insert, unless you know what you're doing.

        Here is the several strategies available when creating a media :

        * file - disk
        * file - database
        * file_url - disk
        * file_url - database
        * file_path - disk
        """

        data = kwargs.copy()
        storage_strategy = cls.get_source_storage_strategy()

        _file = data.get("file")
        _file_url = data.get("file_url")
        _file_path = data.get("file_path")
        _file_fields = list(filter(None, [_file, _file_url, _file_path]))

        if not cls.MEDIA_TYPE:
            raise Exception(
                "registry.Media.MEDIA_TYPE is not set.registry.Media is the base polymorphic media model. You should implement your own, or use one of Media.Image, Media.Audio, Media.Video."
            )
        if not len(_file_fields):
            raise Exception(
                "No 'file', 'file_url' nor 'filepath' field set, can't create"
                " media object"
            )

        if len(_file_fields) > 1:
            raise Exception(
                "Too much source file fields set, can't create media object"
            )

        if _file_url:
            # download remote file data
            req = requests.get(_file_url)
            filename = os.path.split(_file_url)[-1]

            # populate data["file"]
            data["file"] = req.content

            if not data.get("filename"):
                data["filename"] = filename

        elif _file_path:
            # read local file
            with open(_file_path, "rb") as fp:
                data["file"] = fp.read()

            filename = os.path.split(_file_path)[-1]
            if not data.get("filename"):
                data["filename"] = filename

        if data.get("file"):
            if storage_strategy == "database":
                # nothing to do here, stream will be saved on 'file' field
                pass
            elif storage_strategy == "disk":
                # remove 'file' from 'data'
                stream = io.BytesIO(data.pop("file"))
                now = datetime.now()
                source_path_pattern = cls.SOURCE_DISK_STORAGE_PATTERN
                source_path_prefix = Configuration.get("source_path_prefix")
                # Compute source path
                if not source_path_pattern:
                    raise ConfigurationException(
                        "You must set a SOURCE_DISK_STORAGE_PATTERN property"
                        " on your polymorphic class."
                    )

                if not source_path_prefix:
                    raise ConfigurationException(
                        "You must set a source_path_prefix Anyblok"
                        " configuration entry."
                    )

                if not data.get("filename"):
                    raise Exception("No 'filename', can't create media object")

                # compute a new clean and unique file name
                if data.get("filename"):
                    data["filename"] = cls.slugify_filename(
                        data.get("filename")
                    )

                filename, extension = data.get("filename").split(".")

                # compute destination source path
                source_path = source_path_pattern.format(
                    source_path_prefix=source_path_prefix,
                    year=now.year,
                    month=now.month,
                    day=now.day,
                    filename=filename,
                    extension=extension,
                )

                destination_dir, destination_filename = os.path.split(
                    source_path
                )

                # create destination directory if it does not exists yet
                if not os.path.exists(destination_dir):
                    try:
                        os.makedirs(destination_dir, 0o755)
                    except OSError:
                        logger.error(
                            "Creation of the directory %s failed"
                            % destination_dir
                        )
                    else:
                        logger.debug(
                            "Successfully created the directory %s"
                            % destination_dir
                        )

                # write the file
                with open(source_path, "wb") as destf:
                    try:
                        destf.write(stream.read())
                    except OSError:
                        logger.error(
                            "Creation of the file %s failed" % source_path
                        )
                    else:
                        logger.debug(
                            "Successfully created file %s" % source_path
                        )
                        data["file_path"] = source_path

        rec = cls.insert(**data)
        return rec

    def get_source_file_field(self):
        """ Get the source file type of an existing record"""
        if self.file:
            return "file"
        elif self.file_url:
            return "file_url"
        elif self.file_path:
            return "file_path"
        return None

    def get_source_bytes(self):
        """Return bytes from source file field"""
        field = self.get_source_file_field()

        stream = None

        if not field:
            logger.warning("No source file set on %r" % self)
            return
        else:
            if field == "file":
                stream = io.BytesIO(self.file)
            elif field == "file_path":
                with open(self.file_path, "rb") as fp:
                    bits = fp.read()
                    stream = io.BytesIO(bits)
            elif field == "file_url":
                bits = urlopen(self.file_url).read()
                stream = io.BytesIO(bits)
            return stream

    def process(self, **kwargs):
        """Process a source file. This has to be implemented on polymorphic
        class, for example to :

        * generate alternative versions of source file
        * store reference to alternative versions in self.properties
        * set state as 'published'
        """
        raise NotImplementedError(
            "You must implement a method to process source file on your"
            " polymorphic class"
        )

    def __str__(self):
        return ("{self.media_type} {self.filename} {self.state}").format(
            self=self
        )

    def __repr__(self):
        msg = "<Media: {self.media_type} {self.filename} {self.state}>"

        return msg.format(self=self)
