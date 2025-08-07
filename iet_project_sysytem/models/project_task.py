from odoo import models, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'


    date_start = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
