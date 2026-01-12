from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    team_name = fields.Char(string="Team Name")
    date_start = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    status_done = fields.Boolean(string="Done", default=False)

    def write(self, vals):
        print("llllllllllllllllllllllllll")
        if not self.env.context.get('skip_stage_validation') and 'stage_id' in vals:
            for task in self:
                stage = self.env['project.task.type'].browse(vals['stage_id'])
                if stage.required_deadline:
                    date_deadline = vals.get('date_deadline', task.date_deadline)
                    if not date_deadline:
                        raise ValidationError(_("You must fill in 'Deadline Date' before changing stage."))
                if stage.required_allocated:
                    allocated_hours = vals.get('allocated_hours', task.allocated_hours)
                    if not allocated_hours:
                        raise ValidationError(_("You must fill in 'Allocated Hours' before changing stage."))

        res = super(ProjectTask, self).write(vals)
        print("llllllllllllllllllllllllll")

        if self.env.context.get('skip_plan_line_update'):
            return res

        plan_line_model = self.env['project.plan.line']

        for rec in self:
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>")
            plan_line = plan_line_model.search([('task_id', '=', rec.id)], limit=1)
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>",plan_line.id)

            if plan_line:
                print(">>>>>>>>>>>>>>>>>>>>>>>>>>")

                plan_vals = {
                    'status_done': rec.is_closed,
                }
                print(plan_vals)
                if rec.is_closed and not plan_line.actual_end_date:
                    plan_vals['actual_end_date'] = fields.Date.today()
                    print(plan_vals)

                plan_line.with_context(skip_task_update=True).sudo().write(plan_vals)

        return res

    def action_add_timesheet(self):
        """Open timesheet creation form for this task, filtered by current employee"""
        self.ensure_one()
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return {
            'name': 'Add Timesheet',
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'list',
            'target': 'new',
            'domain': [('employee_id', '=', employee.id)],
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
                'default_employee_id': employee.id,
            }
        }
