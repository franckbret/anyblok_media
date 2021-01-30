# This file is a part of the AnyBlok / Media project
#
#    Copyright (C) 2021 Franck Bret <franckbret@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
import os, io
from anyblok.tests.conftest import init_registry_with_bloks
from anyblok import Declarations
from anyblok.config import Configuration


register = Declarations.register
Mixin = Declarations.Mixin
Model = Declarations.Model


@pytest.mark.usefixtures("rollback_registry")
class TestMediaAudioModel:
    """ Test media audio model"""

    def init_registry(self, func):
        self.registry = init_registry_with_bloks(("media-audio",), func)
        return self.registry

    @pytest.fixture(autouse=True, scope="function")
    def define_registry(self):
        def add_in_registry():
            @register(Model.Media)
            class Audio:
                SOURCE_STORAGE_STRATEGY = "disk"
                SOURCE_DISK_STORAGE_PATTERN = "{source_path_prefix}/audio/{year}/{month}/{day}/{filename}.{extension}"

            Configuration.set(
                "source_path_prefix", "/tmp/anyblok_media_tests/"
            )

        self.registry = self.init_registry(add_in_registry)

    def test_media_audio_file_with_storage_strategy_disk(self):
        filename = "sample.ogg"
        dir_path = os.path.join(os.path.dirname(__file__), "media_sample/")
        source_path = dir_path + filename
        assert self.registry.Media.Audio.get_source_storage_strategy() == "disk"

        with open(source_path, "rb") as fp:
            data = fp.read()
            media = self.registry.Media.Audio.create(file=data, filename=filename)
            # Here storage strategy is disk, so media.file must remain empty
            assert media.file is None
            # Source file field should be media.file_path
            assert media.get_source_file_field() == "file_path"
            assert type(media.get_source_bytes()) == io.BytesIO

    def test_media_audio_file_path(self):
        filename = "sample.mp3"
        dir_path = os.path.join(os.path.dirname(__file__), "media_sample/")
        source_path = dir_path + filename
        tag = self.registry.Tag.insert(name="sample", media_type="audio")
        media = self.registry.Media.Audio.create(
            file_path=source_path, filename=filename
        )
        media.tags.append(tag)
        assert media.file_path is not None
        assert media.get_source_file_field() == "file_path"
        assert type(media.get_source_bytes()) == io.BytesIO
