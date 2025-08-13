from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    team_name = fields.Char(string="Team Name", required=True)
    date_start = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")

    def write(self, vals):
        if 'stage_id' in vals:
            for task in self:
                stage = self.env['project.task.type'].browse(vals['stage_id'])

                if stage.required_deadline:
                    date_deadline = vals.get('date_deadline', task.date_deadline)
                    if not date_deadline:
                        raise ValidationError(
                            _("You must fill in 'Deadline Date' before changing stage.")
                        )

                if stage.required_allocated:
                    allocated_hours = vals.get('allocated_hours', task.allocated_hours)
                    if not allocated_hours:
                        raise ValidationError(
                            _("You must fill in 'Allocated Hours' before changing stage.")
                        )

        return super().write(vals)

    def action_add_timesheet(self):
        """Open timesheet creation form for this task, filtered by current employee"""
        self.ensure_one()
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return {
            'name': 'Add Timesheet',
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'list',
            'target': 'new',  # لو عايز popup خليها 'new'
            'domain': [('employee_id', '=', employee.id)],
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
                'default_employee_id': employee.id,
            }
        }

    def _get_tasks_domain(self):
        if self.env.user.has_group("base.group_system") or self.env.user.has_group("project.group_project_manager"):
            return []
        return [('user_ids', 'in', self.env.uid)]
