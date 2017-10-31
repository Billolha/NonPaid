# -*- coding: utf-8 -*-
from odoo.http import request

from odoo import api, fields, models

class ConfigSettingsGoogleContacts(models.TransientModel):

    _inherit = "res.config.settings"
    

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
        ir_config_param.set_param('google_contacts_client_id', client_id)

        client_secret = config.google_contacts_client_secret
        ir_config_param.set_param('google_contacts_client_secret', client_secret)

        uri = self.env['google.service']._get_google_token_uri('contacts', scope=self.env['google.contacts'].get_google_scope() )
        self.google_contacts_uri = uri

    google_contacts_client_id = fields.Char(string="Client ID", default=_default_google_contacts_client_id)
    google_contacts_client_secret = fields.Char(string="Client Secret", default=_default_google_contacts_client_secret)
    google_contacts_authorization_code = fields.Char(string="Authorization Code", default=_default_google_contacts_authorization_code)
    google_contacts_uri = fields.Char(string="Google Contacts URI", compute=_compute_google_contacts_uri)

    @api.model
    def get_values(self):
        res = super(ConfigSettingsGoogleContacts, self).get_values()
        res.update(
            google_contacts_authorization_code=self.env['ir.config_parameter'].sudo().get_param('google_contacts_authorization_code'),
            google_contacts_client_secret=self.env['ir.config_parameter'].sudo().get_param('google_contacts_client_secret'),
            google_contacts_client_id=self.env['ir.config_parameter'].sudo().get_param('google_contacts_client_id'),
            google_contacts_uri=self.env['ir.config_parameter'].sudo().get_param('google_contacts_uri'),
        )
        return res
    
    def set_values(self):
        super(ConfigSettingsGoogleContacts, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        google_contacts_client_id = self.google_contacts_client_id
        google_contacts_client_secret = self.google_contacts_client_secret 
        google_contacts_authorization_code = self.google_contacts_authorization_code
        google_contacts_uri = self.google_contacts_uri
        if google_contacts_authorization_code and google_contacts_authorization_code != ir_config_param.get_param('google_contacts_authorization_code'):
            refresh_token = self.env['google.service'].generate_refresh_token('contacts', config.google_contacts_authorization_code)
            params.set_param('google_contacts_authorization_code', google_contacts_authorization_code)
            params.set_param('google_contacts_refresh_token', refresh_token)
        params.set_param('google_contacts_client_id', google_contacts_client_id)
        params.set_param('google_contacts_client_secret', google_contacts_client_secret)
