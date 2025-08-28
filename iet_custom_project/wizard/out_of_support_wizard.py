from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectOutOfSupportWizard(models.TransientModel):
    _name = 'project.out.of.support.wizard'
    _description = 'Project Stage Change Wizard'

    project_id = fields.Many2one('project.project', string="Project", required=True)
    reason = fields.Text(string="Reason", required=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    is_out_of_support = fields.Boolean(string="Out of Support")
    is_cancel = fields.Boolean(string="Cancel")

    def confirm_out_of_support(self):
        self.ensure_one()

        if not self.project_id:
            raise UserError(_("Please select a project."))

        # تحديد المرحلة الجديدة بناءً على checkbox
        if self.is_out_of_support:
            new_stage = self.env['project.project.stage'].search([('out_of_support', '=', True)], limit=1)
        elif self.is_cancel:
            new_stage = self.env['project.project.stage'].search([('is_cancel', '=', True)], limit=1)
        else:
            raise UserError(_("Please select a stage type (Out of Support or Cancel)."))

        if not new_stage:
            raise UserError(_("No stage found for the selected type."))

        # تحديث المشروع بالمرحلة الجديدة مع bypass context
        self.project_id.with_context(bypass_out_of_support_check=True).write({
            'stage_id': new_stage.id
        })

        # تخزين السبب مع اسم المرحلة
        self.env['out.of.support'].create({
            'project_id': self.project_id.id,
            'reason': self.reason,
            'date': self.date,
            'stage_name': new_stage.name,
            'is_out_of_support': self.is_out_of_support,
            'is_cancel': self.is_cancel,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
            'target': 'main',
        }
