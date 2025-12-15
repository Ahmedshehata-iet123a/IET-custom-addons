{
    'name': 'Project Payment Tracking',
    'version': '1.0',
    'category': 'Project',
    "website": "https://intelligent-experts.com/en/home/",
    'auther': 'IET - SalehElSrief',
    'summary': 'Track payment dates for projects with notifications',
    'depends': ['project', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_payment_views.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': False,
}
