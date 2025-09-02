from odoo import models, fields, api

class ProjectPlanLog(models.Model):
    _name = 'project.log'
    _description = 'Project Stage Log'

    project_id = fields.Many2one('project.project', string='Project', required=True, ondelete='cascade')
    stage_from = fields.Char(string="Stage From")
    stage_to = fields.Char(string="Stage To")
    stage_from_date = fields.Datetime(string="Stage Date From")
    stage_to_date = fields.Datetime(string="Stage Date To", default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Changed By', default=lambda self: self.env.user)