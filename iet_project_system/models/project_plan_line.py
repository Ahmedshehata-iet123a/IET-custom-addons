from odoo import models, fields, api
from datetime import timedelta, datetime
from odoo.exceptions import ValidationError


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
    task_id = fields.Many2one('project.task', string="Linked Task")
    planned_duration = fields.Float(
        string='Planned Duration (Days)',
        compute='_compute_durations',
        store=True,
        help="Duration between planned start and end dates excluding weekends and holidays."
    )
    actual_duration = fields.Float(
        string='Actual Duration (Days)',
        compute='_compute_durations',
        store=True,
        help="Duration between actual start and end dates excluding weekends and holidays."
    )
    milestone_id = fields.Many2one('project.milestone', string='Milestone')

    def assign_milestones_to_plan_lines(self):
        current_milestone = None
        for line in self.sorted(key=lambda l: l.id):
            if line.display_type == 'line_section':
                current_milestone = self.env['project.milestone'].search([
                    ('name', '=', line.name),
                    ('project_id', '=', line.project_id.id)
                ], limit=1)
            elif not line.display_type:
                line.milestone_id = current_milestone.id if current_milestone else False

    @api.depends('planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date', 'project_id')
    def _compute_durations(self):
        for record in self:
            record.planned_duration = 0.0
            record.actual_duration = 0.0

            calendar = record.project_id.resource_calendar_id or self.env.company.resource_calendar_id

            if not calendar:
                continue

            if record.planned_start_date and record.planned_end_date:
                if record.planned_start_date > record.planned_end_date:
                    raise ValidationError("Planned start date cannot be after planned end date.")
                record.planned_duration = self._compute_working_days(
                    record.planned_start_date,
                    record.planned_end_date,
                    calendar
                )

            if record.actual_start_date and record.actual_end_date:
                if record.actual_start_date > record.actual_end_date:
                    raise ValidationError("Actual start date cannot be after actual end date.")
                record.actual_duration = self._compute_working_days(
                    record.actual_start_date,
                    record.actual_end_date,
                    calendar
                )

    def _compute_working_days(self, start_date, end_date, calendar):
        if not start_date or not end_date:
            return 0.0
        start_dt = start_date.replace(tzinfo=None) if isinstance(start_date, datetime) else start_date
        end_dt = end_date.replace(tzinfo=None) if isinstance(end_date, datetime) else end_date
        leaves = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('date_from', '<=', end_dt),
            ('date_to', '>=', start_dt)
        ])
        current_date = start_dt
        working_days = 0.0
        delta = end_dt - start_dt
        for i in range(delta.days + 1):
            day = current_date + timedelta(days=i)
            if day.weekday() in [4, 5]:
                continue
            is_holiday = False
            for leave in leaves:
                leave_start = leave.date_from.replace(tzinfo=None)
                leave_end = leave.date_to.replace(tzinfo=None)
                if leave_start <= day <= leave_end:
                    is_holiday = True
                    break

            if not is_holiday:
                working_days += 1.0
        if delta.seconds > 0:
            hours = delta.seconds / 3600.0
            working_days += hours / 8.0
        return working_days

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
                milestone = self.env['project.milestone'].search([
                    ('name', '=', rec.name),
                    ('project_id', '=', rec.project_id.id)
                ], limit=1)
                if not milestone:
                    milestone = self.env['project.milestone'].create({
                        'name': rec.name,
                        'deadline': rec.planned_end_date,
                        'project_id': rec.project_id.id,
                    })
                if rec.milestone_id != milestone:
                    super(ProjectPlanLine, rec).write({
                        'milestone_id': milestone.id
                    })
