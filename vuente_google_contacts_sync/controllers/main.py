import odoo.http as http
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import base64
import json
import odoo
import re

from odoo.addons.http_routing.models.ir_http import slug

class GoogleContactsAuthController(http.Controller):

    @http.route('/google/contacts/auth', website=True, type='http', auth="public")
    def google_contacts_auth(self, **kw):
        request.env['google.contacts'].cron_sync()
        
        #web?view_type=list&model=res.partner&menu_id=154&action=170#page=0&limit=80&view_type=list&model=res.partner&menu_id=154&action=170        
        
        google_contacts_menu = request.env['ir.model.data'].sudo().get_object('vuente_google_contacts_sync', 'google_contacts_contacts_menu')
        google_contacts_menu_action = request.env['ir.model.data'].sudo().get_object('vuente_google_contacts_sync', 'google_contacts_contact_action')
    
        return werkzeug.utils.redirect("/web?view_type=list&model=res.partner&menu_id=" + str(google_contacts_menu.id) + "&action=" + str(google_contacts_menu_action.id) + "#page=0&limit=80&view_type=list&model=res.partner&menu_id=" + str(google_contacts_menu.id) + "&action=" + str(google_contacts_menu_action.id) )
        
        #return {
	#    'type': 'ir.actions.act_window',
	#    'view_type': 'form',
	#    'view_mode': 'form,tree',
	#    'res_model': 'res.partner',
	#    'target': 'current',
	#    'domain"': [('google_contacts_id','!=', False)]
        #}
