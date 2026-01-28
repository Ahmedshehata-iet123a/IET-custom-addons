from odoo import models, fields, api

class ProjectStage(models.Model):
    _inherit = 'project.project.stage'

    is_stop_workload = fields.Boolean(
        string='Stop Workload Counting',
        help='If checked, days_passed will stop counting when a project enters this stage.'
    )

class Project(models.Model):
    _inherit = 'project.project'

    date_stop_workload = fields.Date(
        string='Date Workload Stopped',
        help='The date when the project entered a stage that stops workload counting.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for project in projects:
            if project.stage_id.is_stop_workload:
                project.date_stop_workload = fields.Date.today()
        return projects

    def write(self, vals):
        if 'stage_id' in vals:
            stage = self.env['project.project.stage'].browse(vals['stage_id'])
            if stage.is_stop_workload:
                vals['date_stop_workload'] = fields.Date.today()
            else:
                vals['date_stop_workload'] = False
        return super().write(vals)
