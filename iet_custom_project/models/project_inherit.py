from odoo import models, fields,_
from odoo.exceptions import UserError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    document_type = fields.Selection([
        ('project_scope', 'Project Scope'),
        ('training', 'Training Document'),
        ('stakeholder', 'Stakeholder'),
        ('uat', 'UAT'),
        ('brd', 'BRD'),
        ('plan', 'Project Plan'),
        ('mom', 'MOM'),
        ('closing', 'Project Closing')
    ], string="Document Type")


class Project(models.Model):
    _inherit = 'project.project'

    industry_id = fields.Many2one('project.industry', string='Industry')
    team_id = fields.Many2one('project.team',string='Team')

    attachment_training_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'project.project'),
            ('document_type', '=', 'training')
        ],
        string="Training Documents",
        context={
            'default_res_model': 'project.project',
            'default_document_type': 'training'
        }
    )

    attachment_stakeholder_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'project.project'),
            ('document_type', '=', 'stakeholder')
        ],
        string="Stakeholder Documents",
        context={
            'default_res_model': 'project.project',
            'default_document_type': 'stakeholder'
        }
    )

    attachment_uat_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'project.project'),
            ('document_type', '=', 'uat')
        ],
        string="UAT Documents",
        context={
            'default_res_model': 'project.project',
            'default_document_type': 'uat'
        }
    )

    attachment_brd_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'project.project'),
            ('document_type', '=', 'brd')
        ],
        string="BRD Documents",
        context={
            'default_res_model': 'project.project',
            'default_document_type': 'brd'
        }
    )

    attachment_plan_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'project.project'),
            ('document_type', '=', 'plan')
        ],
        string="Project Plan Documents",
        context={
            'default_res_model': 'project.project',
            'default_document_type': 'plan'
        }
    )

    attachment_closing_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'project.project'),
            ('document_type', '=', 'closing')
        ],
        string="Project Closing Documents",
        context={
            'default_res_model': 'project.project',
            'default_document_type': 'closing'
        }
    )
    attachment_project_scope_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'project.project'),
            ('document_type', '=', 'project_scope')
        ],
        string="Project Scope Documents",
        context={
            'default_res_model': 'project.project',
            'default_document_type': 'project_scope'
        }
    )

    attachment_mom_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[
            ('res_model', '=', 'project.project'),
            ('document_type', '=', 'mom')
        ],
        string="Project MOM Documents",
        context={
            'default_res_model': 'project.project',
            'default_document_type': 'mom'
        }
    )


    def write(self, vals):
        if 'stage_id' in vals:
            new_stage = self.env['project.project.stage'].browse(vals['stage_id'])

            if 'Project Stage Manager' not in self.env.user.groups_id.mapped('name'):
                for rec in self:
                    missing_fields = []

                    if new_stage.training_document and not rec.attachment_training_ids:
                        missing_fields.append("Training Document")
                    if new_stage.stakeholder and not rec.attachment_stakeholder_ids:
                        missing_fields.append("Stakeholder")
                    if new_stage.uat and not rec.attachment_uat_ids:
                        missing_fields.append("UAT")
                    if new_stage.brd and not rec.attachment_brd_ids:
                        missing_fields.append("BRD")
                    if new_stage.project_plan and not rec.attachment_plan_ids:
                        missing_fields.append("Project Plan")
                    if new_stage.project_closing and not rec.attachment_closing_ids:
                        missing_fields.append("Project Closing")
                    if new_stage.project_scope and not rec.attachment_project_scope_ids:
                        missing_fields.append("Project Scope")



                    if missing_fields:
                        raise UserError(_(
                            "You cannot move to stage '%s' without uploading the required attachments:\n- %s"
                            % (new_stage.name, "\n- ".join(missing_fields))
                        ))

        return super(Project, self).write(vals)

