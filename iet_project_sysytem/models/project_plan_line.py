from odoo import models, fields, api

class ProjectPlanLine(models.Model):
    _name = 'project.plan.line'
    _description = 'Project Plan Line'

    project_id = fields.Many2one('project.project', string='Project')
    name = fields.Char(string='Task Name')
    planned_start_date = fields.Datetime(string='Planned Start Date')
    actual_start_date = fields.Datetime(string='Actual Start Date')
    planned_end_date = fields.Datetime(string='Planned End Date')
    actual_end_date = fields.Datetime(string='Actual End Date')
    task_owner= fields.Text(string='Task Owner')
    status = fields.Text(string='Status')
    comments = fields.Text(string='Comments')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

