from odoo import models, fields


class ProjectTeam(models.Model):
    _name = 'project.team'
    _description = 'Project Team'

    name = fields.Char(string="Team Name", required=True)
    team_member_ids = fields.Many2many('hr.employee', string='Team Members', required=True)
