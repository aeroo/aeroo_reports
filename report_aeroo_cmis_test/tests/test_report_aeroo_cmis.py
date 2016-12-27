# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from openerp.tests import common


class TestReportAerooCmis(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestReportAerooCmis, cls).setUpClass()
        cls.backend = cls.env['aeroo.dms.backend'].create({
            'name': 'Local Alfresco Server',
            'location': 'http://127.0.0.1:8080/alfresco/cmisatom',
            'username': 'admin',
            'password': 'admin',
        })
        cls.backend.update_repository_list()
        cls.report = cls.env.ref('report_aeroo_sample.aeroo_sample_report_id')
        repo = cls.backend.repository_ids[0].get_repository()

        cls.folder_name = 'test_aeroo_reports'
        for doc_name in ('template.odt', 'template_en.odt'):
            try:
                repo.getObjectByPath('/%s/%s' % (cls.folder_name, doc_name))
            except:
                folders = repo.rootFolder.getChildren().getResults()
                test_folder = next(
                    (f for f in folders if f.name == cls.folder_name), None)
                if not test_folder:
                    test_folder = repo.createFolder(
                        repo.rootFolder, cls.folder_name)
                repo.createDocumentFromString(
                    doc_name,
                    parentFolder=test_folder,
                    contentString=base64.decodestring(
                        cls.report.report_rml_content))

        cls.report.write({
            'in_format': 'oo-odt',
            'tml_source': 'dms',
            'dms_repository_id': cls.backend.repository_ids[0].id,
            'dms_path': '/%s/template.odt' % cls.folder_name,
            'report_rml': False,
            'report_rml_content': False,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'My Partner',
        })

    def test_01_generate_report(self):
        self.partner.print_report('sample_report', {})

    def prepare_report_by_lang(self):
        self.report.write({
            'tml_source': 'lang',
            'lang_eval': 'o.lang',
        })
        self.report.write({'report_line_ids': [(0, 0, {
            'lang_id': self.env.ref('base.lang_en').id,
            'template_source': 'dms',
            'template_location': '/%s/template_en.odt' % self.folder_name,
        })]})

    def test_02_generate_report_by_lang(self):
        self.prepare_report_by_lang()
        self.partner.print_report('sample_report', {})

    def test_03_generate_report_exception(self):
        # Generate the report a first time in order to store the template
        # in the Odoo database
        self.partner.print_report('sample_report', {})
        self.backend.password = 'wrong_password'
        self.partner.print_report('sample_report', {})

    def test_04_generate_report_by_lang_exception(self):
        self.prepare_report_by_lang()
        self.partner.print_report('sample_report', {})
        self.backend.password = 'wrong_password'
        self.partner.print_report('sample_report', {})
