from odoo import models, fields, api


class ProjectPlanLine(models.Model):
    _name = 'project.plan.line'
    _description = 'Project Plan Line'

    project_id = fields.Many2one('project.project', string='Project')
    name = fields.Char(string='Task Name')
    planned_start_date = fields.Datetime(string='Planned Start Date')
    actual_start_date = fields.Datetime(string='Actual Start Date')
    planned_end_date = fields.Datetime(string='Planned End Date')
    actual_end_date = fields.Datetime(string='Actual End Date')
    task_owner = fields.Text(string='Task Owner')
    status = fields.Text(string='Status')
    comments = fields.Text(string='Comments')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._create_milestone_if_section()
        return record

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._create_milestone_if_section()
        return res

    def _create_milestone_if_section(self):
        for rec in self:
            if rec.display_type == 'line_section' and rec.project_id:
                milestone_exists = self.env['project.milestone'].search([
                    ('name', '=', rec.name),
                    ('project_id', '=', rec.project_id.id)
                ], limit=1)
                if not milestone_exists:
                    self.env['project.milestone'].create({
                        'name': rec.name,
                        'deadline': rec.planned_end_date,
                        'project_id': rec.project_id.id,
                    })
