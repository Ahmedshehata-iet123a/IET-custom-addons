{
    'name': 'IET Deleted Records Tracker',
    'version': '18.0.1.0.0',
    'summary': 'Track and log deleted records from project tasks',
    'description': """
        This module creates a log of deleted records.
        Currently tracking: project.task
    """,
    'category': 'Hidden/Tools',
    'author': 'IET',
    'depends': ['base', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/deleted_record_log_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}