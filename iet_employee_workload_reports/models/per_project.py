from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class EmployeePerProjectReport(models.Model):
    """تقرير حمل الموظفين حسب المشروع"""
    _name = 'employee.per.project.report'
    _description = 'Employee Per Project Report'
    _order = 'date_from desc'

    name = fields.Char(string='Report Name', required=True)
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    line_ids = fields.One2many('employee.per.project.report.line', 'report_id', string='Report Lines')

    @api.model
    def default_get(self, fields_list):
        res = super(EmployeePerProjectReport, self).default_get(fields_list)
        today = fields.Date.today()
        first_day = today.replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)

        res.update({
            'date_from': first_day,
            'date_to': last_day,
            'name': 'Per Project Report - ' + today.strftime('%B %Y')
        })
        return res

    def action_generate_report(self):
        """توليد تقرير الموظفين حسب المشروع"""
        self.ensure_one()
        self.line_ids.unlink()

        # جلب الموظفين النشطين
        employees = self.env['hr.employee'].search([('active', '=', True)])

        for employee in employees:
            # حساب ساعات السعة الإجمالية للموظف
            capacity_hours = self._calculate_capacity_hours(employee)

            # جلب المشاريع التي عمل عليها الموظف في هذه الفترة
            timesheets = self.env['account.analytic.line'].search([
                ('employee_id', '=', employee.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('project_id', '!=', False),
            ])

            # تجميع الساعات حسب المشروع
            project_hours = {}
            for timesheet in timesheets:
                project_id = timesheet.project_id.id
                if project_id not in project_hours:
                    project_hours[project_id] = 0
                project_hours[project_id] += timesheet.unit_amount

            # إنشاء سطر لكل مشروع
            for project_id, assigned_hours in project_hours.items():
                load_percentage = (assigned_hours / capacity_hours * 100) if capacity_hours > 0 else 0

                # تحديد الحالة
                if load_percentage >= 100:
                    status = 'overload'
                elif load_percentage >= 80:
                    status = 'normal'
                else:
                    status = 'under'

                self.env['employee.per.project.report.line'].create({
                    'report_id': self.id,
                    'employee_id': employee.id,
                    'project_id': project_id,
                    'capacity_hours': capacity_hours,
                    'assigned_hours': assigned_hours,
                    'load_percentage': load_percentage,
                    'status': status,
                })

        return True

    def _calculate_capacity_hours(self, employee):
        """حساب ساعات السعة للموظف"""
        calendar = employee.resource_calendar_id or self.env.company.resource_calendar_id

        total_hours = 0
        current_date = self.date_from
        while current_date <= self.date_to:
            # تجاهل الجمعة (4) والسبت (5)
            if current_date.weekday() not in (4, 5):
                start_dt = datetime.combine(current_date, datetime.min.time())
                end_dt = datetime.combine(current_date, datetime.max.time())
                hours = calendar.get_work_hours_count(start_dt, end_dt, compute_leaves=False)
                total_hours += hours
            current_date += timedelta(days=1)

        # خصم إجازات الموظف
        leave_hours = self._calculate_leave_hours(employee)
        return total_hours - leave_hours

    def _calculate_leave_hours(self, employee):
        """حساب ساعات الإجازات"""
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_from),
        ])

        total_hours = 0
        for leave in leaves:
            start = max(leave.date_from.date(), self.date_from)
            end = min(leave.date_to.date(), self.date_to)

            if start <= end:
                calendar = employee.resource_calendar_id or self.env.company.resource_calendar_id
                hours = calendar.get_work_hours_count(
                    datetime.combine(start, datetime.min.time()),
                    datetime.combine(end, datetime.max.time()),
                    compute_leaves=False,
                    domain=[('calendar_id', '=', calendar.id)]
                )
                total_hours += hours

        return total_hours


class EmployeePerProjectReportLine(models.Model):
    _name = 'employee.per.project.report.line'
    _description = 'Employee Per Project Report Line'
    _order = 'employee_id, project_id'

    report_id = fields.Many2one('employee.per.project.report', string='Report', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    capacity_hours = fields.Float(string='Capacity Hours', digits=(10, 2))
    assigned_hours = fields.Float(string='Assigned Hours', digits=(10, 2))
    load_percentage = fields.Float(string='Load %', digits=(10, 2))
    status = fields.Selection([
        ('under', 'Under'),
        ('normal', 'Normal'),
        ('overload', 'Overload'),
    ], string='Status', required=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department', store=True)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Job Position', store=True)
