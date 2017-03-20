# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import openerp.addons.connector.backend as backend

aeroo_dms = backend.Backend('aeroo_dms')
aeroo_dms1000 = backend.Backend(parent=aeroo_dms, version='1.0')
