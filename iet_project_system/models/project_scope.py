from odoo import fields,models

class ProjectScope(models.Model):
    _name = 'project.scope'
    _description = 'Project Scope Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Scope Name", required=True)