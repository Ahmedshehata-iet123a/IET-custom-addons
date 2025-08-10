from odoo import models, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'

    team_name = fields.Char(string="Team Name", required=True)
    date_start = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
