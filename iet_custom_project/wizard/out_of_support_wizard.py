from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectOutOfSupportWizard(models.TransientModel):
    _name = 'project.out.of.support.wizard'
    _description = 'Out of Support Reason'

    project_id = fields.Many2one('project.project', string="Project", required=True)
    new_stage_id = fields.Many2one('project.project.stage', string="New Stage", required=True)
    stage_name = fields.Char(string="Stage Name", readonly=True)
    reason = fields.Text(string="Reason", required=True)
    date = fields.Date(string="Out of Support Date", required=True, default=fields.Date.today)

    @api.onchange('new_stage_id')
    def _onchange_stage_id(self):
        if self.new_stage_id:
            self.stage_name = self.new_stage_id.name

    def confirm_out_of_support(self):
        self.ensure_one()

        if not self.project_id or not self.new_stage_id:
            raise UserError(_("Could not find the project or the new stage."))

        self.env['out.of.support'].create({
            'project_id': self.project_id.id,
            'reason': self.reason,
            'date': self.date,
            'stage_name': self.new_stage_id.name,
        })

        self.project_id.with_context(bypass_out_of_support_check=True).write({
            'stage_id': self.new_stage_id.id
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
            'target': 'main',
        }

