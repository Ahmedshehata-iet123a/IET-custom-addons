{
    'name': 'IET Project Status Report',
    'version': '18.0.1.0.0',
    'summary': 'List view for projects grouped by status',
    'category': 'Project',
    'author': 'IET',
    'website': 'https://intelligent-experts.com',
    'license': 'LGPL-3',
    'depends': ['project', 'iet_custom_project'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_status_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
