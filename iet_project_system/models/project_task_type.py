from odoo import models, fields


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    generate_tasks = fields.Boolean(string="Generate Tasks")
    required_deadline = fields.Boolean(string="Required Deadline")
    required_allocated = fields.Boolean(string="Required Allocated")
