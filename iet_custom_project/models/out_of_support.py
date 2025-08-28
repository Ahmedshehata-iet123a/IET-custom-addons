# In a new file, e.g., out_of_support.py
from odoo import models, fields


class OutOfSupport(models.Model):
    _name = 'out.of.support'
    _description = 'Project Out of Support Log'
    _order = 'date desc, id desc'

    reason = fields.Text(string="Reason", required=True)
    date = fields.Date(string="Out of Support Date", required=True)

    project_id = fields.Many2one(
        'project.project',
        string="Project",
        required=True,
        ondelete='cascade'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user
    )
    stage_name = fields.Char(string="Stage Name")
    is_out_of_support = fields.Boolean(string="Out of Support Reason")
    is_cancel = fields.Boolean(string="Cancel Reason")
