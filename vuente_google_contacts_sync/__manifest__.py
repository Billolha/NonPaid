{
    'name': "Vuente Google Contact Sync",
    'version': "1.2.0",
    'author': "Vuente",
    'category': "Tools",
    'summary':'Download contacts from google contacts',
    'license':'LGPL-3',
    'data': [
        'views/res_partner_views.xml',
        'views/config_settings_views.xml',
        'views/google_contacts_views.xml',
        'views/res_users_views.xml',
        'security/ir.model.access.csv',
        'data/ir.cron.csv',
    ],
    'demo': [],
    'depends': ['google_account','crm'],
    'images':[
        'static/description/1.jpg',
    ],
    'installable': True,
}