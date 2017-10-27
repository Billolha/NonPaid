# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import json

from odoo import api, fields, models

class CRMLeadGoogleContacts(models.Model):

    _inherit = "crm.lead"
    
    google_contacts_id = fields.Char(string="Google Contacts ID")
    google_contacts_account = fields.Char(string="Google Contacts Account")