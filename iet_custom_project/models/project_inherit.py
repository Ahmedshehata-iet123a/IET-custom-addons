from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
import logging

_logger = logging.getLogger(__name__)


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
    
    document_date = fields.Date(string="Document Date", default=fields.Date.context_today)


class Project(models.Model):
    _inherit = 'project.project'

    devlop_team_id = fields.Many2one('project.team', string='Development Team', tracking=True, ondelete='set null')
    team_helpdesk_id = fields.Many2one('team.helpdesk', string='Team', tracking=True, ondelete='set null')
    start_project_date = fields.Date("Start Project Date", required=False, tracking=True)
    end_project_date = fields.Date("End Project Date", required=False, tracking=True)

    free_support_start_date = fields.Date("Free Support Start Date", tracking=True)
    free_support_end_date = fields.Date("Free Support End Date", tracking=True)

    contract_project_start_date = fields.Date("Contract Project Start Date", tracking=True)
    contract_project_end_date = fields.Date("Contract Project End Date", tracking=True)

    industry_id = fields.Many2one('project.industry', string='Industry', tracking=True)
    implementation_owner_ids = fields.Many2many(
        'hr.employee',
        'project_implementation_owner_rel',
        'project_id',
        'employee_id',
        string='Implementation Owners',
        tracking=True,
        domain=[
            ('active', '=', True),
            '|',
            ('department_id', '=', False),
            ('department_id.name', '!=', 'Development')
        ],
        help='Employees responsible for project implementation (excluding Development department)'
    )

    development_owner_ids = fields.Many2many(
        'hr.employee',
        'project_development_owner_rel',
        'project_id',
        'employee_id',
        string='Development Owners',
        tracking=True,
        domain=[
            ('active', '=', True),
            ('department_id.name', '=', 'Development')
        ],
        help='Employees from Development department responsible for project development'
    )

    @api.constrains(
        'start_project_date', 'end_project_date',
        'free_support_start_date', 'free_support_end_date',
        'contract_project_start_date', 'contract_project_end_date'
    )
    def _check_dates(self):
        for rec in self:
            if rec.start_project_date and rec.end_project_date:
                if rec.start_project_date > rec.end_project_date:
                    raise ValidationError("End Project Date must be after Start Project Date.")

            if rec.free_support_start_date and rec.free_support_end_date:
                if rec.free_support_start_date > rec.free_support_end_date:
                    raise ValidationError("Free Support end date must be after start date.")

            if rec.contract_project_start_date and rec.contract_project_end_date:
                if rec.contract_project_start_date > rec.contract_project_end_date:
                    raise ValidationError("Contract Project end date must be after start date.")

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

    out_of_support_log_ids = fields.One2many(
        'out.of.support',
        'project_id',
        string="Out of Support Logs"
    )

    @api.constrains('stage_id')
    def _check_out_of_support_stage(self):
        for record in self:
            if record.stage_id.out_of_support and not self._context.get('bypass_out_of_support_check'):
                last_record = self.env['out.of.support'].search([
                    ('project_id', '=', record.id)
                ], order='date desc, id desc', limit=1)

                raise UserError(_(
                    "Cannot move project '%s' to stage '%s' without providing "
                    "a reason. Please use the 'Set Out of Support' action instead."
                    % (record.name, record.stage_id.name)
                ))

            if record.stage_id.is_cancel and not self._context.get('bypass_out_of_support_check'):
                last_record = self.env['out.of.support'].search([
                    ('project_id', '=', record.id)
                ], order='date desc, id desc', limit=1)
                raise UserError(_(
                    "Cannot move project '%s' to stage '%s' without providing a cancel reason."
                    % (record.name, record.stage_id.name)
                ))

    def action_set_out_of_support_stage(self):
        self.ensure_one()
        return {
            'name': _('Set Project Stage'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.out.of.support.wizard',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
            },
            'view_mode': 'form',
        }

    def write(self, vals):
        if 'stage_id' in vals:
            new_stage = self.env['project.project.stage'].browse(vals['stage_id'])
            if 'Project Stage Manager' not in self.env.user.groups_id.mapped('name'):
                missing_fields = []
                if new_stage.training_document and not self.attachment_training_ids:
                    missing_fields.append("Training Document")
                if new_stage.stakeholder and not self.attachment_stakeholder_ids:
                    missing_fields.append("Stakeholder")
                if new_stage.uat and not self.attachment_uat_ids:
                    missing_fields.append("UAT")
                if new_stage.brd and not self.attachment_brd_ids:
                    missing_fields.append("BRD")
                if new_stage.project_plan and not self.attachment_plan_ids:
                    missing_fields.append("Project Plan")
                if new_stage.project_closing and not self.attachment_closing_ids:
                    missing_fields.append("Project Closing")
                if new_stage.project_scope and not self.attachment_project_scope_ids:
                    missing_fields.append("Project Scope")

                if missing_fields:
                    raise UserError(_(
                        "You cannot move to stage '%s' without uploading the required attachments:\n- %s"
                        % (new_stage.name, "\n- ".join(missing_fields))
                    ))

        _logger.info("--- Calling super().write() for vals: %s ---", vals)
        return super(Project, self).write(vals)
