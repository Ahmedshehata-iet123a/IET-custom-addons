from odoo import models, fields


class Industry(models.Model):
    _name = 'project.industry'
    _description = 'Project Industry'

    name = fields.Char(string='Industry Name', required=True)
