# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AerooDmsBackendRepository(models.Model):
    """Aeroo DMS Backend Repository"""

    _name = 'aeroo.dms.backend.repository'
    _description = __doc__

    backend_id = fields.Many2one(
        'aeroo.dms.backend', 'DMS Backend', required=True)
    name = fields.Char(required=True)
    repository_id = fields.Char(required=True)
    active = fields.Boolean(
        'Active', related='backend_id.active', readonly=True)

    _sql_constraints = [(
        'unique_dms_backend_repository', 'unique(name, repository_id)',
        'The DMS repositoryId must be unique.'
    )]

    @api.multi
    def name_get(self):
        return [
            (r.id, "%s / %s" % (self.backend_id.name, self.name))
            for r in self
        ]

    @api.multi
    def get_repository(self):
        self.ensure_one()
        adapter = self.backend_id.get_adapter()
        return adapter.get_repository(self.repository_id)

    @api.multi
    def read_document_from_path(self, path):
        adapter = self.backend_id.get_adapter()
        return adapter.read_document_from_path(self.repository_id, path)
