{
    "name": "Iet stage custom project",
    "summary": """Iet stage custom project""",
    "description": """ """,
    "author": "IET | Ahmed Shehata",
    "website": "https://intelligent-experts.com/en/home/",
    "version": "18.0.0.1.0",
    "depends": [
        'project','base','odoo_website_helpdesk'

    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/project_stage.xml",
        "views/project_team.xml",
        "views/project_industry.xml",
        "views/project_inherit.xml",
        "wizard/out_of_support_wizard.xml",

    ],
    "installable": True,
}
