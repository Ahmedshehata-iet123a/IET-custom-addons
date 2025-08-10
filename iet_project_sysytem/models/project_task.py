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
