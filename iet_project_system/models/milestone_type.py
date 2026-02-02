from odoo import models, fields, api

class MileStone(models.Model):
    _name = 'milestone.type'
    _description = 'milestone type'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Name', required=True)