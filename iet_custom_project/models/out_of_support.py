# In a new file, e.g., out_of_support.py
from odoo import models, fields


class OutOfSupport(models.Model):
    _name = 'out.of.support'
    _description = 'Project Out of Support Log'
    _order = 'date desc, id desc'  # To show the latest records first

    reason = fields.Text(string="Reason", required=True)
    date = fields.Date(string="Out of Support Date", required=True)

    # حقل الربط Many2one مع المشروع
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        required=True,
        ondelete='cascade'  # If project is deleted, delete these logs too
    )
    # حقل لتسجيل المستخدم الذي قام بالإجراء
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user
    )
    stage_name = fields.Char(string="Stage Name")
