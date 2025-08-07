{
    'name': 'IET Project System',
    'version': '1.0',
    'depends': ['project'],
     "website": "https://intelligent-experts.com/en/home/",
    'auther': 'IET - SalehElSrief',
    'category': 'Project',
    'description': 'Add Project Plan tab with tasks and milestones',
    'data': [
        'security/ir.model.access.csv',
        'views/project_project_views.xml',
        'views/project_task_type.xml',
        'views/project_task.xml',
    ],
    'installable': True,
    'application': False,
}
