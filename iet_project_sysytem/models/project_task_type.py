from odoo import models, fields


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'


    generate_tasks = fields.Boolean(string="Generate Tasks")
