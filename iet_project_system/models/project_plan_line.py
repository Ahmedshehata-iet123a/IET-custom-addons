from odoo import models, fields, api
from datetime import timedelta, datetime
from odoo.exceptions import ValidationError


class ProjectPlanLine(models.Model):
    _name = 'project.plan.line'
    _description = 'Project Plan Line'

    project_id = fields.Many2one('project.project', string='Project')
    name = fields.Char(string='Task Name')
    planned_start_date = fields.Date(string='Planned Start Date')
    actual_start_date = fields.Date(string='Actual Start Date')
    planned_end_date = fields.Date(string='Planned End Date')
    actual_end_date = fields.Date(string='Actual End Date')
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
    status_done = fields.Boolean(string='Done ✅', default=False)
    milestone_type = fields.Selection([
        ('gap_analysis', 'Gap Analysis'),
        ('implementation', 'Implementation'),
        ('training', 'Training')
    ], string="Milestone Type")
    milestone_weight = fields.Integer(string="Weight (%)")

    delay_days = fields.Float(string='Delay (Days)', digits=(10, 1), compute="_compute_delay_days", store=True)

    sequence = fields.Integer(string='Sequence', default=10)

    @api.depends('planned_end_date', 'actual_end_date')
    def _compute_delay_days(self):
        for rec in self:
            rec.delay_days = 0
            if rec.planned_end_date and rec.actual_end_date:
                current_date = rec.planned_end_date
                actual_date = rec.actual_end_date
                if actual_date > current_date:
                    start_loop = current_date + timedelta(days=1)
                    end_loop = actual_date
                    sign = 1
                elif actual_date < current_date:
                    start_loop = actual_date + timedelta(days=1)
                    end_loop = current_date
                    sign = 0
                else:
                    # Same day
                    continue

                delay = 0
                curr = start_loop
                while curr <= end_loop:
                    if curr.weekday() not in (4, 5):
                        delay += 1
                    curr += timedelta(days=1)

                rec.delay_days = delay * sign



    @api.onchange('status_done')
    def _onchange_status_done(self):
        for line in self:
            if line.task_id:
                if line.status_done:
                    done_stage = self.env['project.task.type'].search([
                        ('fold', '=', True)
                    ], limit=1)
                    if done_stage:
                        line.task_id.stage_id = done_stage.id
                        line.task_id.is_closed = True
                # else:
                # Optional: move back to first stage if unchecked
                # first_stage = self.env['project.task.type'].search([], limit=1, order='sequence')
                # if first_stage:
                #     line.task_id.stage_id = first_stage.id

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
    # @api.depends('planned_start_date', 'planned_end_date','project_id')
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

        start_dt = start_date if isinstance(start_date, datetime) else datetime.combine(start_date, datetime.min.time())
        end_dt = end_date if isinstance(end_date, datetime) else datetime.combine(end_date, datetime.min.time())

        leaves = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('date_from', '<=', end_dt),
            ('date_to', '>=', start_dt)
        ])

        working_days = 0.0
        delta = end_dt - start_dt

        for i in range(delta.days + 1):
            day_dt = start_dt + timedelta(days=i)

            # weekend
            if day_dt.weekday() in [4, 5]:
                continue

            # check if holiday
            is_holiday = False
            for leave in leaves:
                leave_start = leave.date_from.replace(tzinfo=None)
                leave_end = leave.date_to.replace(tzinfo=None)
                if leave_start <= day_dt <= leave_end:
                    is_holiday = True
                    break

            if not is_holiday:
                working_days += 1.0

        # جزء الساعات لو موجودة
        if delta.seconds > 0:
            hours = delta.seconds / 3600.0
            working_days += hours / 8.0

        return working_days

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._create_milestone_if_section()
        if 'actual_end_date' in vals and not record.display_type:
            record.write({'actual_end_date': vals['actual_end_date']})  # Trigger the write logic to sync section
        return record

    def write(self, vals):
        # We need to run the milestone date sync even if skip_task_update is present,
        # but we should avoid infinite loops.
        res = super().write(vals)

        # Skip only the standard task sync back logic, but allow Milestone sync
        skip_task_sync = self.env.context.get('skip_task_update')

        if 'actual_end_date' in vals or 'status_done' in vals:
            for line in self:
                if not line.display_type and line.project_id and line.milestone_id:
                    # Logic: If all tasks in this milestone are done, 
                    # sync the milestone row's date from the last task.

                    # Find all sibling tasks (not sections) for this milestone
                    siblings = self.env['project.plan.line'].search([
                        ('project_id', '=', line.project_id.id),
                        ('milestone_id', '=', line.milestone_id.id),
                        ('display_type', '=', False)
                    ], order='id asc')

                    if not siblings:
                        continue

                    # Check if all tasks in this milestone are done
                    all_done = all(s.status_done for s in siblings)

                    # Only update milestone if ALL tasks are done
                    milestone_date = False
                    if all_done:
                        # Get the last task that was marked done (chronologically)
                        done_tasks = siblings.filtered(lambda s: s.status_done)
                        if done_tasks:
                            last_done_task = done_tasks.sorted(lambda s: s.write_date, reverse=True)[0]
                            milestone_date = last_done_task.actual_end_date

                    # Find the section line for this milestone
                    section_line = self.env['project.plan.line'].search([
                        ('project_id', '=', line.project_id.id),
                        ('milestone_id', '=', line.milestone_id.id),
                        ('display_type', '=', 'line_section')
                    ], limit=1)

                    if section_line:
                        # Update section line actual end date and status
                        update_vals = {'actual_end_date': milestone_date}

                        # Check if all tasks in this milestone are done
                        all_done = all(s.status_done for s in siblings)
                        if all_done:
                            update_vals['status_done'] = True

                        section_line.write(update_vals)

                        # Update the milestone deadline
                        if section_line.milestone_id:
                            section_line.milestone_id.deadline = milestone_date

        if skip_task_sync:
            return res

        if 'status_done' in vals:
            for line in self:
                if line.task_id:
                    if 'status_done' in vals:
                        for line in self:
                            if line.task_id:
                                if vals['status_done']:
                                    update_vals = {
                                        'is_closed': True,
                                        'status_done': True,
                                        'state': '1_done',
                                    }

                                    line.task_id.with_context(skip_plan_line_update=True).sudo().write(update_vals)

                                else:
                                    last_open_stage = self.env['project.task.type'].search(
                                        [('fold', '=', False)], order='sequence', limit=1
                                    )
                                    update_vals = {
                                        'is_closed': False,
                                        'status_done': False,
                                        'state': '01_in_progress',
                                    }
                                    # if last_open_stage:
                                    #     update_vals['stage_id'] = last_open_stage.id

                                    line.task_id.with_context(skip_plan_line_update=True).sudo().write(update_vals)

                            line.project_id._compute_completion_percent()

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
