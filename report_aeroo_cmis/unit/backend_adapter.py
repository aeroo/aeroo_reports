# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from cStringIO import StringIO

from openerp.addons.connector.unit.backend_adapter import CRUDAdapter
from cmislib.model import CmisClient


class DmsAdapter(CRUDAdapter):

    def auth(self):
        backend_record = self.backend_record
        self.client = CmisClient(
            backend_record.location,
            backend_record.username, backend_record.password)

    def get_repositories(self):
        return {
            r['repositoryId']: r['repositoryName'] for r in
            self.client.getRepositories()
        }

    def get_repository(self, repository_id):
        return self.client.getRepository(repository_id)

    def read_document_from_path(self, repository_id, path):
        repo = self.client.getRepository(repository_id)
        doc = repo.getObjectByPath(path)
        output = StringIO()
        output.write(doc.getContentStream().read())
        data = output.getvalue()
        version = doc.getProperties()['cmis:versionLabel']
        return data, version
