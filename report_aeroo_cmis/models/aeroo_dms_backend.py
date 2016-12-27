# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.addons.connector.connector import ConnectorEnvironment
from openerp.addons.connector.session import ConnectorSession
from ..unit.backend_adapter import DmsAdapter


class AerooDmsBackend(models.Model):
    """Aeroo DMS Backend"""

    _name = 'aeroo.dms.backend'
    _description = __doc__
    _backend_type = 'aeroo_dms'
    _inherit = 'connector.backend'

    name = fields.Char(required=True)
    version = fields.Selection(
        selection_add=[('1.0', '1.0')], default='1.0')
    location = fields.Char('Location', required=True)
    active = fields.Boolean('Active', default=True)
    username = fields.Char(
        'Username', required=True,
        groups="connector.group_connector_manager")
    password = fields.Char(
        'Password', required=True,
        groups="connector.group_connector_manager")

    repository_ids = fields.One2many(
        'aeroo.dms.backend.repository', 'backend_id', 'Repositories')

    @api.multi
    def update_repository_list(self):
        self.ensure_one()
        adapter = self._get_base_adapter()
        adapter.auth()
        all_repositories = adapter.get_repositories()
        existing_repositories = {
            r.repository_id: r for r in self.repository_ids
        }

        for repo_id, repo_name in all_repositories.items():
            if repo_id not in existing_repositories:
                self.env['aeroo.dms.backend.repository'].create({
                    'backend_id': self.id,
                    'repository_id': repo_id,
                    'name': repo_name,
                })
            elif existing_repositories[repo_id].name != repo_name:
                existing_repositories[repo_id].name = repo_name

    @api.multi
    def _get_base_adapter(self):
        """
        Get an adapter to test the backend connection
        """
        self.ensure_one()
        env = self.env
        session = ConnectorSession(env.cr, env.uid, context=env.context)
        environment = ConnectorEnvironment(self, session, None)
        return DmsAdapter(environment)

    @api.multi
    def get_adapter(self):
        self.ensure_one()
        adapter = self._get_base_adapter()
        adapter.auth()
        return adapter
