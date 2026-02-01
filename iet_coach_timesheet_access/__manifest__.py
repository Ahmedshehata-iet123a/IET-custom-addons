{
    'name': 'Coach Timesheet View',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Allow coaches to view their employees timesheets',
    'description': """
        This module allows coaches to view timesheets of their assigned employees
        through a wizard interface.
    """,
    'depends': ['hr', 'hr_timesheet', 'hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/coach_timesheet_wizard_views.xml',
        'views/groups.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}