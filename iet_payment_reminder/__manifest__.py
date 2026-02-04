{
    'name': 'Project Payment Tracking',
    'version': '1.0',
    'category': 'Project',
    "website": "https://intelligent-experts.com/en/home/",
    'auther': 'IET - SalehElSrief',
    'summary': 'Track payment dates for projects with notifications',
    'depends': ['project', 'mail'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/project_payment_views.xml',
        'views/project_views.xml',
        'views/payment_wizard_views.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
}
