from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class EmployeeWorkloadReport(models.Model):
    _name = 'employee.workload.report'
    _description = 'Employee Workload Report'
    _order = 'create_date desc'

    name = fields.Char(string='Report Name', required=True)
    project_ids = fields.Many2many('project.project', string='Projects')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    line_ids = fields.One2many('employee.workload.report.line', 'report_id', string='Workload Lines')

    @api.model
    def default_get(self, fields_list):
        res = super(EmployeeWorkloadReport, self).default_get(fields_list)
        today = fields.Date.today()
        res.update({
            'name': 'Workload Report - ' + today.strftime('%Y-%m-%d')
        })
        return res

    def action_generate_report(self):
        self.ensure_one()
        self.line_ids.unlink()

        # تحديد المشاريع المستهدفة
        project_domain = []
        if self.project_ids:
            project_domain.append(('id', 'in', self.project_ids.ids))

        projects = self.env['project.project'].search(project_domain)

        for project in projects:
            metrics = self._calculate_project_metrics(project)
            project_vals = {
                'report_id': self.id,
                'project_id': project.id,
                'is_project_line': True,
                'status': 'normal',
                **metrics
            }
            self.env['employee.workload.report.line'].create(project_vals)

            timesheet_domain = [('project_id', '=', project.id), ('employee_id', '!=', False)]
            if self.employee_id:
                timesheet_domain.append(('employee_id', '=', self.employee_id.id))

            ts_data = self.env['account.analytic.line'].read_group(
                timesheet_domain,
                ['unit_amount'],
                ['employee_id']
            )

            for data in ts_data:
                employee = self.env['hr.employee'].browse(data['employee_id'][0])
                assigned_hours = data['unit_amount']

                self.env['employee.workload.report.line'].create({
                    'report_id': self.id,
                    'project_id': project.id,
                    'employee_id': employee.id,
                    'assigned_hours': assigned_hours,
                    'is_project_line': False,
                    'status': 'normal',
                })

        return True

    def _count_working_days(self, start_date, end_date):
        if not start_date or not end_date:
            return 0
        if start_date > end_date:
            return 0

        days = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() not in (4, 5):  # 4=Friday, 5=Saturday
                days += 1
            current_date += timedelta(days=1)
        return days

    def _calculate_project_metrics(self, project):
        today = fields.Date.today()

        planned_duration = self._count_working_days(project.date_start, project.date)

        end_count = project.date_stop_workload or today
        days_passed = self._count_working_days(project.date_start, end_count)

        expected_progress = 0
        if planned_duration > 0:
            expected_progress = min((days_passed / planned_duration) * 100, 100.0)

        actual_progress = project.completion_percent if hasattr(project, 'completion_percent') else 0
        delay_days = project.all_delay_days

        if delay_days <= project.threshold_on_track and delay_days < project.threshold_at_risk:
            schedule_status = 'on_track'
        elif delay_days == project.threshold_at_risk and delay_days <= project.threshold_delayed:
            schedule_status = 'at_risk'
        else:
            schedule_status = 'delayed'

        return {
            'planned_duration': planned_duration,
            'days_passed': days_passed,
            'expected_progress': expected_progress,
            'actual_progress': actual_progress,
            'delay_days': delay_days,
            'schedule_status': schedule_status
        }


class EmployeeWorkloadReportLine(models.Model):
    _name = 'employee.workload.report.line'
    _description = 'Employee Workload Report Line'
    _order = 'project_id, is_project_line desc, employee_id'

    report_id = fields.Many2one('employee.workload.report', string='Report', required=True, ondelete='cascade')
    is_project_line = fields.Boolean(string='Is Project Section', default=False)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    project_id = fields.Many2one('project.project', string='Project')
    project_stage_id = fields.Many2one('project.project.stage', string='Project Stage', related='project_id.stage_id',
                                       store=True)
    planned_duration = fields.Float(string='Planned Duration (Days)', digits=(10, 1))
    days_passed = fields.Float(string='Days Passed', digits=(10, 1))
    expected_progress = fields.Float(string='Expected %', digits=(10, 1))
    actual_progress = fields.Float(string='Actual %', digits=(10, 1))
    delay_days = fields.Float(string='Delay (Days)', digits=(10, 1))
    schedule_status = fields.Selection([
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('delayed', 'Delayed')
    ], string='Schedule Status')

    assigned_hours = fields.Float(string='Assigned Hours', digits=(10, 2))
    load_percentage = fields.Float(string='Load %', digits=(10, 2))
    status = fields.Selection([
        ('under', 'Under'),
        ('normal', 'Normal'),
        ('overload', 'Overload'),
    ], string='Status', required=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department',
                                    store=True)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Job Position', store=True)
    assigned_hours_display = fields.Char(
        string="Assigned Hours",
        compute="_compute_assigned_hours_display"
    )

    @api.depends('assigned_hours')
    def _compute_assigned_hours_display(self):
        for rec in self:
            minutes = int(rec.assigned_hours * 60)
            h = minutes // 60
            m = minutes % 60
            rec.assigned_hours_display = f"{h}:{m:02d}"
