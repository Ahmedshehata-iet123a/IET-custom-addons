from odoo import models, fields

class ProjectStakeholder(models.Model):
    _name = 'project.stakeholder'
    _description = 'Project Stakeholder'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    job_title = fields.Char(string='Job Title')
    email = fields.Char(string='Email')
    mobile = fields.Char(string='Mobile')
