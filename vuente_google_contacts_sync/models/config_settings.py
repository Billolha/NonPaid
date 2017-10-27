# -*- coding: utf-8 -*-
from odoo.http import request

from odoo import api, fields, models

class ConfigSettingsGoogleContacts(models.TransientModel):

    _inherit = "base.config.settings"

    def _default_google_contacts_authorization_code(self):
        authorization_code = self.env['ir.config_parameter'].get_param('google_contacts_authorization_code')
        return authorization_code

    def _default_google_contacts_client_id(self):
        google_contacts_client_id = self.env['ir.config_parameter'].get_param('google_contacts_client_id')
        return google_contacts_client_id

    def _default_google_contacts_client_secret(self):
        google_contacts_client_secret = self.env['ir.config_parameter'].get_param('google_contacts_client_secret')
        return google_contacts_client_secret
    
    @api.one
    @api.depends('google_contacts_client_id','google_contacts_client_secret')
    def _compute_google_contacts_uri(self):
        ir_config_param = self.env['ir.config_parameter']
        config = self
        client_id = config.google_contacts_client_id
        ir_config_param.set_param('google_contacts_client_id', client_id, groups=['base.group_system'])

        client_secret = config.google_contacts_client_secret
        ir_config_param.set_param('google_contacts_client_secret', client_secret, groups=['base.group_system'])

        uri = self.env['google.service']._get_google_token_uri('contacts', scope=self.env['google.contacts'].get_google_scope() )
        self.google_contacts_uri = uri

    google_contacts_client_id = fields.Char(string="Client ID", default=_default_google_contacts_client_id)
    google_contacts_client_secret = fields.Char(string="Client Secret", default=_default_google_contacts_client_secret)
    google_contacts_authorization_code = fields.Char(string="Authorization Code", default=_default_google_contacts_authorization_code)
    google_contacts_uri = fields.Char(string="Google Contacts URI", compute=_compute_google_contacts_uri)

    @api.model
    def set_google_contacts_authorization_code(self, ids):
        ir_config_param = self.env['ir.config_parameter']
        config = self.browse(ids[0])
        auth_code = config.google_contacts_authorization_code
        if auth_code and auth_code != ir_config_param.get_param('google_contacts_authorization_code'):
            refresh_token = self.env['google.service'].generate_refresh_token('contacts', config.google_contacts_authorization_code)
            ir_config_param.set_param('google_contacts_authorization_code', auth_code, groups=['base.group_system'])
            ir_config_param.set_param('google_contacts_refresh_token', refresh_token, groups=['base.group_system'])

    @api.model
    def set_google_contacts_client_id(self, ids):
        ir_config_param = self.env['ir.config_parameter']
        config = self.browse(ids[0])
        client_id = config.google_contacts_client_id
        ir_config_param.set_param('google_contacts_client_id', client_id, groups=['base.group_system'])

    @api.model
    def set_google_contacts_client_secret(self, ids):
        ir_config_param = self.env['ir.config_parameter']
        config = self.browse(ids[0])
        client_secret = config.google_contacts_client_secret
        ir_config_param.set_param('google_contacts_client_secret', client_secret, groups=['base.group_system'])
