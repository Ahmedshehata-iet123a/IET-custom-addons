# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Image in Kanban',
    'version': '18.0.0.1',
    'category': 'project',
    'sequence': 6,
    'summary': 'Project Image showing in Kanban',
    'description': "This module for showing image in project kanban",
    'author': 'Creative Dev Co.,Ltd.',
    'website': 'https://creativedev.co.th/en',
    'depends': ['base', 'project'],
    'data': [
        'views/project_project_view.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
}
