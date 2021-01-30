# This file is a part of the AnyBlok / Media project
#
#    Copyright (C) 2021 Franck Bret <franckbret@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
from anyblok.blok import Blok
from logging import getLogger
logger = getLogger(__name__)


class MediaBlok(Blok):
    """Media blok
    """
    version = "1.0.0"
    author = "Franck BRET"
    required = ["anyblok-core", "anyblok-mixins", "anyblok-workflow"]

    @classmethod
    def import_declaration_module(cls):
        from . import models # noqa

    @classmethod
    def reload_declaration_module(cls, reload):
        from . import models
        reload(models)
