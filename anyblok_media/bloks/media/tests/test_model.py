# This file is a part of the AnyBlok / Media project
#
#    Copyright (C) 2021 Franck Bret <franckbret@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest
import os


@pytest.mark.usefixtures("rollback_registry")
class TestMediaModel:
    """ Test media model"""

    @pytest.fixture(autouse=True, scope="function")
    def define_registry(self, rollback_registry):
        self.registry = rollback_registry

    def test_media_storage_strategy(self):
        assert self.registry.Media.SOURCE_STORAGE_STRATEGIES == [
            "database",
            "disk",
        ]
        assert self.registry.Media.SOURCE_STORAGE_STRATEGY is None
        assert self.registry.Media.get_source_storage_strategy() is None
        self.registry.Media.SOURCE_STORAGE_STRATEGY = "database"
        assert (
            self.registry.Media.SOURCE_STORAGE_STRATEGY
            == self.registry.Media.get_source_storage_strategy()
            == "database"
        )

    def test_media_slugify_filename(self):
        filename = "The \$%+&!#/ - C'est L'été.extension"
        slugified = self.registry.Media.slugify_filename(filename)

        slugified_random_suffix = self.registry.Media.slugify_filename(filename, random_suffix=True)
        assert filename != slugified != slugified_random_suffix
        assert len(slugified_random_suffix) > len(slugified)

    def test_media_create_fail_without_media_type(self):
        binary_data = os.urandom(1024)

        with pytest.raises(Exception) as excinfo:
            media_db_storage = self.registry.Media.create(file=binary_data, filename="a.ext")
