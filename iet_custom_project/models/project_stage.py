from odoo import models, fields

class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    training_document = fields.Boolean(string="Training Document")
    stakeholder = fields.Boolean(string="Stakeholder")
    uat = fields.Boolean(string="UAT")
    brd = fields.Boolean(string="BRD")
    project_plan = fields.Boolean(string="Project Plan")
    project_closing = fields.Boolean(string="Project Closing")
    project_scope = fields.Boolean(string="Project Scope")
    out_of_support = fields.Boolean(string="Out of Support")
    is_cancel = fields.Boolean(string="Cancel")