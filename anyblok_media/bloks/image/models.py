# This file is a part of the AnyBlok / Media project
#
#    Copyright (C) 2021 Franck Bret <franckbret@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Image model
"""
import io
import os
from datetime import datetime
from logging import getLogger

from PIL import Image as PilImage
from PIL.ExifTags import TAGS

import pyexiv2

from anyblok import Declarations
from anyblok.config import Configuration, ConfigurationException

logger = getLogger(__name__)

register = Declarations.register
Model = Declarations.Model
Mixin = Declarations.Mixin


@register(Model)
class Media:
    @classmethod
    def get_media_types(cls):
        res = super(Media, cls).get_media_types()
        res.update(dict(image="Image"))
        return res


@register(Model)
class Tag:
    @classmethod
    def get_media_types(cls):
        res = super(Tag, cls).get_media_types()
        res.update(dict(image="Image"))
        return res


@register(Model.Media, tablename=Model.Media)
class Image(Model.Media):
    MEDIA_TYPE = "image"
    PROCESS_PARAMS = []
    DESTINATION_PATH_PATTERN = ""
    URL_PATTERN = ""

    @classmethod
    def get_file_metadata(cls, stream):
        """Reads an image stream and return a metadata dict"""
        if not stream:
            logger.warning(
                "You should pass a 'stream' object to use that method"
            )
            return
        # Read metadata from file
        meta = dict()

        with pyexiv2.ImageData(stream.read()) as img:
            exif_data = img.read_exif()
            # TODO: explore iptc data
            # iptc_data = img.read_iptc()
            xmp_data = img.read_xmp()

            # Extract common metadata
            xmp_keys = [
                "title",
                "description",
                "creator",
                "contributor",
                "publisher",
                "rights",
                "date",
            ]
            if len(xmp_data):
                for k in xmp_keys:
                    v = xmp_data.get("Xmp.dc.%s" % k)
                    if v:
                        meta[k] = v

            exif_keys = [
                {"datetime": "Exif.Image.DateTimeOriginal"},
                {"creator": "Exif.Image.Artist"},
                {"rights": "Exif.Image.Copyright"},
            ]
            if len(exif_data):
                for key in exif_keys:
                    for k, v in key.items():
                        val = exif_data.get(v)
                        if val:
                            meta[k] = val
        return meta

    @classmethod
    def set_file_metadata(cls, stream=None, metadata=None):
        """Given a stream and metadata, returns a tagged stream"""
        if not stream:
            logger.warning(
                "You should pass a 'stream' object to use that method"
            )
            return
        if not metadata:
            logger.warning(
                "You should pass a 'metadata' dict to use that method"
            )
            return
        meta = dict()
        exif_keys = {"datetime": "Exif.Image.DateTimeOriginal"}
        exif_meta = dict()
        xmp_keys = {
            "title": "Xmp.xmp.Title",
            "description": "Xmp.xmp.Description",
            "creator": "Xmp.xmp.Creator",
            "contributor": "Xmp.xmp.Contributor",
            "publisher": "Xmp.xmp.Publisher",
            "rights": "Xmp.xmp.Rights",
        }
        xmp_meta = dict()
        for k, v in metadata.items():
            if k in exif_keys.keys():
                exif_meta[exif_keys.get(k)] = v
            if k in xmp_keys.keys():
                xmp_meta[xmp_keys.get(k)] = v

        if exif_meta or xmp_meta:
            with pyexiv2.ImageData(stream.getvalue()) as img:
                if exif_meta:
                    img.modify_exif(exif_meta)
                if xmp_meta:
                    img.modify_xmp(xmp_meta)
                return img.get_bytes()

    @classmethod
    def before_update_orm_event(cls, mapper, connection, target):
        target.edit_date = datetime.now()
        storage_strategy = cls.get_source_storage_strategy()
        stream = target.get_source_bytes()
        tagged_stream = cls.set_file_metadata(
            stream=stream, metadata=target.meta
        )
        field = target.get_source_file_field()

        if storage_strategy == "disk" and field == "file_path":
            with open(target.file_path, "rb+") as f:
                if tagged_stream:
                    with pyexiv2.ImageData(tagged_stream) as img:
                        f.seek(0)
                        f.write(img.get_bytes())
                    f.seek(0)
        elif storage_strategy == "database" and field == "file":
            if tagged_stream:
                target.file = tagged_stream.get_bytes()

    def get_image_object_from_byte(self):
        """Return a Pil object from self"""

        stream = self.get_source_bytes()

        return PilImage.open(stream)

    def format_transformation_properties(self):
        """Build a properties dict of image transformation
        and destination properties for generating files on disk.

        To use it we need to define:

        * "media_path_prefix", a configuration entry that describe media_path prefix
          on disk.

        At class level (on you polymorphic class), you need to define some
        constants:

        * "PROCESS_PARAMS", a list of dict that describe transformation rules
        * "DESTINATION_PATH_PATTERN", a format pattern to compute a destination
          path
        * "URL_PATTERN", a format pattern to compute a url to serve the file

        For DESTINATION_PATH_PATTERN and URL_PATTERN formatting you can use the
        followings variables:

        * "name", the 'preset' name, a unique string
        * "width", the 'width' of the generated image
        * "height", the 'height' of the generated image
        * "extension", the file extension of the generated image
        * "file_format", the image file format, see
          https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
        * "tranformation_mode", one of ['resize', 'crop', 'preserve']
        * "self", the instance object of your polymorphic class

        You can implement your own method on your polymorphic class if you
        need more control.
        """
        if not self.PROCESS_PARAMS:
            logger.warning("You should set PROCESS_PARAMS to use that method")
            return

        if not self.DESTINATION_PATH_PATTERN:
            logger.warning(
                "You should set DESTINATION_PATH_PATTERN to use that method"
            )
            return

        if not self.URL_PATTERN:
            logger.warning("You should set URL_PATTERN to use that method")
            return

        params = self.PROCESS_PARAMS
        dest_pattern = self.DESTINATION_PATH_PATTERN
        url_pattern = self.URL_PATTERN
        properties = dict()
        media_path = Configuration.get("media_path_prefix")
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day

        for name, item in params.items():
            size = item.get("size")
            width = item.get("width")
            height = item.get("height")
            extension = item.get("extension")
            file_format = item.get("file_format")
            transformation_mode = item.get("transformation_mode")

            path = dest_pattern.format(
                self=self,
                name=name,
                media_path_prefix=media_path,
                filename=self.filename,
                size=size,
                extension=extension,
                year=year,
                month=month,
                day=day,
            )
            url = url_pattern.format(
                self=self,
                name=name,
                filename=self.filename,
                width=width,
                height=height,
                extension=extension,
                year=year,
                month=month,
                day=day,
            )
            properties[name] = dict(
                width=width,
                height=height,
                path=path,
                url=url,
                file_format=file_format,
                transformation_mode=transformation_mode,
                extension=extension,
            )
        return properties

    def __resize(self, img, size):
        generated = img.resize(size, PilImage.ANTIALIAS)
        return generated

    def __crop(self, img, size):
        width = size[0]
        height = size[1]

        if img.width >= img.height:
            generated = img.resize(
                (int(height * img.width / img.height), height),
                PilImage.ANTIALIAS,
            )
            generated = generated.crop(
                (
                    int((generated.width - width) / 2),
                    0,
                    int((generated.width + width) / 2),
                    height,
                )
            )
        else:
            generated = img.resize(
                (width, int(width * img.width / img.height)),
                PilImage.ANTIALIAS,
            )
            generated = generated.crop(
                (
                    0,
                    int((generated.height - height) / 2),
                    width,
                    int((generated.height + height) / 2),
                )
            )
        return generated

    def __preserve(self, img, size):
        generated = img.copy()
        generated.thumbnail(size, PilImage.ANTIALIAS)
        return generated

    def process(self, **kwargs):
        """Set self.properties through format_transformation_properties(), then
        generate each image version as defined in self.properties
        """
        if not self.DESTINATION_PATH_PATTERN:
            logger.warning(
                "You should set DESTINATION_PATH_PATTERN to use that method"
            )
            return

        if not self.PROCESS_PARAMS:
            logger.warning("You should set PROCESS_PARAMS to use that method")
            return

        self.properties = self.format_transformation_properties()

        for k, v in self.properties.items():
            self.generate(name=k, params=v)
        return self

    def generate(self, name, params):
        """Transform source image and save it on disk"""
        source = self.get_image_object_from_byte()
        file_format = params.get("file_format")
        path = params.get("path")
        transformation_mode = params.get("transformation_mode")
        width = params.get("width")
        height = params.get("height")

        if transformation_mode not in ["resize", "preserve", "crop"]:
            logger.warning(
                "Can not generate image, '%s' is an invalid "
                "'transformation_mode'" % transformation_mode
            )
            return

        # Ensure path prefix exists
        prefix, filename = os.path.split(path)
        if not os.path.exists(prefix):
            os.makedirs(prefix)

        if transformation_mode == "resize":
            generated = self.__resize(source, (width, height))
        if transformation_mode == "preserve":
            generated = self.__preserve(source, (width, height))
        if transformation_mode == "crop":
            generated = self.__crop(source, (width, height))

        # If file is saved through pil.save() we lose metadata from source..
        # At this point set_file_metadata for each file version
        imageBytes = io.BytesIO()
        generated.save(imageBytes, format=file_format)
        stream_meta = None
        if self.meta:
            stream_meta = self.set_file_metadata(
                stream=imageBytes, metadata=self.meta
            )
        if stream_meta:
            with open(path, "wb+") as f:
                with pyexiv2.ImageData(stream_meta) as img:
                    f.seek(0)
                    f.write(img.get_bytes())
                f.seek(0)
        else:
            generated.save(path, format=file_format)

    def grab_metadata_from_source(self):
        stream = self.get_source_bytes()
        metadata = self.get_file_metadata(stream)
        return metadata
