from odoo import models, fields, api, _
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

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

    def _cron_free_support_expiry_reminder(self):
        """Send reminder to the Team Leader 7 days before Free Support ends."""
        today = fields.Date.today()
        seven_days_later = today + timedelta(days=7)

        projects = self.search([
            ('free_support_end_date', '=', seven_days_later),
            ('team_helpdesk_id', '!=', False),
            ('team_helpdesk_id.team_lead_id', '!=', False)
        ])

        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            activity_type = self.env['mail.activity.type'].search([('name', '=', 'To Do')], limit=1)

        for project in projects:
            team_lead = project.team_helpdesk_id.team_lead_id
            try:
                self.env['mail.activity'].create({
                    'res_id': project.id,
                    'res_model_id': self.env['ir.model']._get_id('project.project'),
                    'activity_type_id': activity_type.id if activity_type else False,
                    'summary': _('Free Support ending in 7 days'),
                    'note': _('The Free Support for project "%s" is ending on %s. Please take necessary actions.') % (project.name, project.free_support_end_date),
                    'date_deadline': today,
                    'user_id': team_lead.id,
                })
                _logger.info("Activity created for Team Leader %s on project %s", team_lead.name, project.name)
            except Exception as e:
                _logger.error("Failed to create activity for %s on project %s: %s", team_lead.name, project.name, str(e))
