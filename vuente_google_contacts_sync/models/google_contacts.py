# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import werkzeug
import json
import urllib.request, urllib.error, urllib.parse
import requests
import math
from odoo.http import request
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, exception_to_unicode
from odoo.exceptions import RedirectWarning, UserError
from odoo.addons.google_account.models.google_service import GOOGLE_TOKEN_ENDPOINT, TIMEOUT
from lxml import etree
from odoo.tools.translate import _
import dicttoxml

from odoo import api, fields, models



class GoogleContacts(models.Model):

    _name = "google.contacts"
    _description = "Google Contacts"
    
    fake_field = fields.Char(string="Fake Field")
    s_model = fields.Selection([('crm.lead','Leads'), ('res.partner','Partners')], string="Import as", default="crm.lead")
    
    def need_authorize(self):
        return (self.env.user.google_contacts_rtoken is False or not self.env.user.google_contacts_rtoken)

    def authorize_google_uri(self, from_url='http://www.openerp.com'):
        url = self.env['google.service']._get_authorize_uri(from_url, 'contacts', scope=self.get_google_scope())
        return url

    @api.model
    def set_all_tokens(self, authorization_code):
        _logger.error("all token set")
        gs_pool = self.env['google.service']
        all_token = gs_pool._get_google_token_json(authorization_code, 'contacts')
        
        vals = {}
        vals['google_contacts_rtoken'] = all_token.get('refresh_token')
        vals['google_contacts_token_validity'] = datetime.now() + timedelta(seconds=all_token.get('expires_in'))
        vals['google_contacts_token'] = all_token.get('access_token')
        self.env.user.write(vals)
        
    @api.multi
    def g_contact_download(self):
        _logger.error("WOLHERROR : g contact Download ")
        self.ensure_one()
        
        self.env.user.google_contacts_last_sync_date = datetime.now()
        if self.need_authorize():
            my_from_url = request.httprequest.host_url + "google/contacts/auth"
            url = self.authorize_google_uri(from_url=my_from_url)
            _logger.error(url)
            return {'type': 'ir.actions.act_url', 'url': url, 'target': 'self'}
        
        self.upload_contact_to_external()
        _logger.error("WOLHERROR : Downloaded ")


    def get_google_scope(self):
        return 'http://www.google.com/m8/feeds/contacts/'

    @api.model
    def get_access_token(self, scope=None):
        ir_config = self.env['ir.config_parameter']
        '''
        google_contacts_refresh_token = ir_config.get_param('google_contacts_refresh_token')
        if not google_contacts_refresh_token:
            if self.env['res.users']._is_admin([self.env.uid]):
                model, action_id = self.env['ir.model.data'].get_object_reference('base_setup', 'action_general_configuration')
                msg = _("You haven't configured 'Authorization Code' generated from google, Please generate and configure it .")
                raise openerp.exceptions.RedirectWarning(msg, action_id, _('Go to the configuration panel'))
            else:
                raise UserError(_("Google Contacts is not yet configured. Please contact your administrator."))
        '''
        google_contacts_client_id = ir_config.get_param('google_contacts_client_id')
        google_contacts_client_secret = ir_config.get_param('google_contacts_client_secret')

        google_contacts_refresh_token = self.env.user.google_contacts_rtoken
        #For Getting New Access Token With help of old Refresh Token

        data = werkzeug.url_encode(dict(client_id=google_contacts_client_id,
                                     refresh_token=google_contacts_refresh_token,
                                     client_secret=google_contacts_client_secret,
                                     grant_type="refresh_token",
                                     scope=scope or 'http://www.google.com/m8/feeds/contacts/'))
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        _logger.error("WOLHERROR : token set")
        _logger.error(data)
        try:
            #req = urllib.request.Request('https://accounts.google.com/o/oauth2/token', data, headers)
            #content = urllib.request.urlopen(req, timeout=TIMEOUT).read()
            req = requests.post(GOOGLE_TOKEN_ENDPOINT, data=data, headers=headers, timeout=TIMEOUT)
            req.raise_for_status()
        except urllib.error.HTTPError:
            if user_is_admin:
                dummy, action_id = self.env['ir.model.data'].get_object_reference('base_setup', 'action_general_configuration')
                msg = _("Something went wrong during the token generation. Please request again an authorization code .")
                raise RedirectWarning(msg, action_id, _('Go to the configuration panel'))
            else:
                raise UserError(_("Google Drive is not yet configured. Please contact your administrator."))
        #content = json.loads(content)
        #return content.get('access_token')
        return req.json().get('access_token')

    @api.model
    def upload_contact_to_external(self):
        gs_pool = self.env['google.service']
        
        access_token = self.get_access_token()
        headers = {'Authorization': 'Bearer ' + access_token, 'GData-Version': '3.0','Content-type': 'application/atom+xml'}
        
        nb_customer = self.env['res.partner'].search_count([('customer', '=', True)])
        
        _logger.error("WOLHERROR : Number of customers :  " + str(nb_customer))
        if nb_customer > 0 :
            existing_contacts = self.env['res.partner'].search([('customer', '=', True)])
            MY_NAMESPACES = {'atom' : 'http://www.w3.org/2005/Atom','gd' : 'http://schemas.google.com/g/2005'}
            xml = etree.Element('{%s}entry' % MY_NAMESPACES['atom'],nsmap=MY_NAMESPACES)
            category = etree.Element('{%s}category' % MY_NAMESPACES['atom'],nsmap=MY_NAMESPACES)
            category.set('scheme','http://schemas.google.com/g/2005#kind') 
            category.set('term','http://schemas.google.com/contact/2008#contact')
            xml.append(category)
                
            for contact in existing_contacts:
                
                _logger.error("WOLHERROR : responses json ")
                _logger.error(contact.name)
                name = etree.Element('{%s}name' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                fullname = etree.Element('{%s}fullName' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                fullname.text = contact.name
                name.append(fullname)
                xml.append(name)
                postaladdress = etree.Element('{%s}structuredPostalAddres' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                postaladdress.set('rel','http://schemas.google.com/g/2005#work')
                postaladdress.set('primary','true')
                
                if contact.company_type == 'company':
                    org = etree.Element('{%s}organization' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                    org.set('rel','http://schemas.google.com/g/2005#work')
                    orgname = etree.Element('{%s}orgName' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                    orgname.text = contact.name
                    org.append(orgname)
                    xml.append(org)

                if contact.parent_id:
                    company_search = self.env['res.partner'].search([('id','=', contact.parent_id)])
                    if company_search:
                        org = etree.Element('{%s}organization' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                        org.set('rel','http://schemas.google.com/g/2005#work')
                        orgname = etree.Element('{%s}orgName' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                        orgname.text = company_search.name
                        org.append(orgname)
                        xml.append(org)
                        
                if contact.email:
                    email = etree.Element('{%s}email' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                    email.set('address',contact.email)
                    email.set('rel','http://schemas.google.com/g/2005#work')
                    xml.append(email)
                    
                if contact.mobile:
                    mobile = etree.Element('{%s}phoneNumber' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                    mobile.set('rel','http://schemas.google.com/g/2005#work')
                    mobile.set('primary','true')
                    mobile.text = contact.mobile
                    xml.append(mobile)
                if contact.phone:
                    phone = etree.Element('{%s}phoneNumber' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                    phone.set('rel','http://schemas.google.com/g/2005#work')
                    phone.text = contact.phone
                    xml.append(phone)
                if contact.street:
                    
                    street = etree.Element('{%s}street' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                    street.text = contact.street
                    if contact.street2:
                        
                        street.text += ' ' + contact.street2
                    postaladdress.append(street)
                if contact.city :
                    
                    city = etree.Element('{%s}city' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                    city.text = contact.city
                    postaladdress.append(city)
                if contact.zip :
                    
                    zip = etree.Element('{%s}zip' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                    zip.text = contact.zip
                    postaladdress.append(zip)
                if contact.state_id:
                    
                    #Find the corresponding state in out database
                    state_search = self.env['res.country.state'].search([('id','=', contact.state_id.id)])
                    if state_search:
                        region = etree.Element('{%s}region' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                        region.text = state_search[0].name
                        postaladdress.append(region)
                
                if contact.country_id:
                    #Find the corresponding country in out database
                    country_search = self.env['res.country'].search([('id','=', contact.country_id.id)])
                    if country_search:
                        country = etree.Element('{%s}country' % MY_NAMESPACES['gd'],nsmap=MY_NAMESPACES)
                        country.text = country_search[0].name
                        country.set('code',country_search[0].code)
                        postaladdress.append(region)
                
                xml.append(postaladdress)
                _logger.error("WOLHERROR : responses json ")
                
                
                
                
                _logger.error(etree.tostring(xml))
                
            url = "https://www.google.com/m8/feeds/contacts/scopea.fr/full"
            xml_string = etree.tostring(xml)
            
            
            res = requests.post(url, data=xml_string,headers=headers)
            _logger.error(res.content)
            res.raise_for_status()
            status = res.status_code

                

    @api.model
    def cron_sync(self):
        gs_pool = self.env['google.service']

# debut modif
#        access_token = self.env.user.google_contacts_token
        access_token = self.get_access_token()
        _logger.error("WOLHERROR : token accessed " + access_token)
        dic_partner = {}
        for res in self.env['res.partner'].search_read([('is_company','=',True)]) :
            dic_partner[res['name']] = res['id']
# fin modif
        
        headers = {'Authorization': 'Bearer ' + access_token, 'GData-Version': '3.0'}

        #Get the 'My Contacts' Group
        response_string = requests.get("https://www.google.com/m8/feeds/contacts/scopea.fr/full/?v=3.0&alt=json", headers=headers)
        
        google_contacts_group_json = response_string.json()
        _logger.error("WOLHERROR : responses json ")
        _logger.error(json.dumps(google_contacts_group_json, indent=4, sort_keys=True))
        # WOLH : Not necessary for directory
        #my_contacts_group = google_contacts_group_json['feed']['entry'][0]['id']['$t']
        
        
        #Fetch the first 25 and get the total results in the process
        start_index = 1
        response_string = requests.get("https://www.google.com/m8/feeds/contacts/scopea.fr/full?v=3.0&alt=json&start-index=" + str(start_index), headers=headers)

        google_contacts_json = response_string.json()
        _logger.error(json.dumps(google_contacts_group_json, indent=4, sort_keys=True))
        total_results = google_contacts_json['feed']['openSearch$totalResults']['$t']

        num_pages = math.ceil( int(total_results) / 25)
        _logger.error("WOLHERROR : Nb Pages " + str(num_pages))
        for page in range(1, int(num_pages) + 1):
            _logger.error("WOLHERROR : Page " + str(page))
            account_email = google_contacts_json['feed']['id']['$t'] 
        
            for contact in google_contacts_json['feed']['entry']:    
                if 'gd$name' not in contact:
                    continue
            
                contact_id = contact['id']['$t']
            
                g_contact_dict = {'google_contacts_id': contact_id, 'customer': False, 'google_contacts_account': account_email}

                g_contact_dict['name'] = contact['gd$name']['gd$fullName']['$t']

# debut modif
                if 'gd$organization' in contact and 'gd$orgName' in contact['gd$organization'][0]:
                    soc_name = contact['gd$organization'][0]['gd$orgName']['$t']
                    if soc_name not in dic_partner :
                        partner_id = self.env['res.partner'].create({'name': soc_name, 'is_company': True, 'customer': False })
                        dic_partner[soc_name] = partner_id.id
                        g_contact_dict['parent_id'] = partner_id.id
# fin modif

            
                if 'gd$email' in contact:
                    g_contact_dict['email'] = contact['gd$email'][0]['address']

                if 'gd$phoneNumber' in contact:
                    g_contact_dict['phone'] = contact['gd$phoneNumber'][0]['$t']
            
                if 'gd$structuredPostalAddress' in contact:
                    if 'gd$street' in contact['gd$structuredPostalAddress'][0]:
                        g_contact_dict['street'] = contact['gd$structuredPostalAddress'][0]['gd$street']['$t']

                    if 'gd$city' in contact['gd$structuredPostalAddress'][0]:
                        g_contact_dict['city'] = contact['gd$structuredPostalAddress'][0]['gd$city']['$t']

                    if 'gd$region' in contact['gd$structuredPostalAddress'][0]:
                        state = contact['gd$structuredPostalAddress'][0]['gd$region']['$t']
                    
                        #Find the corresponding state in out database
                        state_search = self.env['res.country.state'].search([('name','=', state)])
                        if state_search:
                            g_contact_dict['state_id'] = state_search[0].id

                    if 'gd$country' in contact['gd$structuredPostalAddress'][0]:
                        country = contact['gd$structuredPostalAddress'][0]['gd$country']['$t']

                        #Find the corresponding country in out database
                        country_search = self.env['res.country'].search([('name','=', country)])
                        if country_search:
                            g_contact_dict['country_id'] = country_search[0].id
                existing_contact = self.env['res.partner'].search([('google_contacts_id', '=', contact_id)])
                if len(existing_contact) > 0:
                    #Update existing partner
                    existing_contact.write(g_contact_dict)
                else:
                    #Create new partner
                    self.env['res.partner'].create(g_contact_dict)

            #Fetch the content for the next page
            start_index += 25
            response_string = requests.get("https://www.google.com/m8/feeds/contacts/scopea.fr/full?v=3.0&alt=json&start-index=" + str(start_index), headers=headers)
            google_contacts_json = response_string.json()

