from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class EmployeeWorkloadReport(models.Model):
    _name = 'employee.workload.report'
    _description = 'Employee Workload Report'
    _order = 'date_from desc'

    name = fields.Char(string='Report Name', required=True)
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    project_id = fields.Many2one('project.project', string='Project')
    line_ids = fields.One2many('employee.workload.report.line', 'report_id', string='Workload Lines')

    @api.model
    def default_get(self, fields_list):
        res = super(EmployeeWorkloadReport, self).default_get(fields_list)
        today = fields.Date.today()
        first_day = today.replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)

        res.update({
            'date_from': first_day,
            'date_to': last_day,
            'name': 'Workload Report - ' + today.strftime('%B %Y')
        })
        return res

    def action_generate_report(self):
        """توليد تقرير الأحمال للموظفين"""
        self.ensure_one()

        # حذف السطور القديمة
        self.line_ids.unlink()

        # جلب الموظفين
        if self.project_id:
            # موظفين المشروع المحدد
            tasks = self.env['project.task'].search([
                ('project_id', '=', self.project_id.id),
                ('user_ids', '!=', False)
            ])
            # جمع كل الموظفين من المهام
            employees = self.env['hr.employee']
            for task in tasks:
                employees |= task.user_ids.mapped('employee_id')
        else:
            # كل الموظفين النشطين
            employees = self.env['hr.employee'].search([('active', '=', True)])

        employees = employees.filtered(lambda e: e.active)

        for employee in employees:
            # حساب ساعات السعة
            capacity_hours = self._calculate_capacity_hours(employee)

            # حساب الساعات المسندة من التايم شيت
            assigned_hours = self._calculate_assigned_hours(employee)

            # حساب نسبة الحمل
            load_percentage = (assigned_hours / capacity_hours * 100) if assigned_hours > 0 else 0

            # تحديد الحالة
            if load_percentage >= 100:
                status = 'overload'
            elif load_percentage >= 80:
                status = 'normal'
            else:
                status = 'under'

            # إنشاء سطر التقرير
            self.env['employee.workload.report.line'].create({
                'report_id': self.id,
                'employee_id': employee.id,
                'capacity_hours': capacity_hours,
                'assigned_hours': assigned_hours,
                'load_percentage': load_percentage,
                'status': status,
            })

        return True

    def _calculate_capacity_hours(self, employee):
        """ساعات السعة = ساعات العمل - إجازات الموظف الشخصية مع تجاهل الجمعة والسبت"""
        calendar = employee.resource_calendar_id or self.env.company.resource_calendar_id

        total_hours = 0
        current_date = self.date_from
        while current_date <= self.date_to:
            # تجاهل الجمعة (4) والسبت (5)
            if current_date.weekday() not in (4, 5):
                start_dt = datetime.combine(current_date, datetime.min.time())
                end_dt = datetime.combine(current_date, datetime.max.time())
                hours = calendar.get_work_hours_count(start_dt, end_dt, compute_leaves=False)
                _logger.info("Employee %s - Date %s - Work Hours: %s", employee.name, current_date, hours)
                total_hours += hours
            current_date += timedelta(days=1)

        # خصم إجازات الموظف الشخصية
        leave_hours = self._calculate_leave_hours(employee)
        _logger.info("Employee %s - Total Capacity Hours: %s, Leave Hours: %s", employee.name, total_hours, leave_hours)

        return total_hours - leave_hours

    def _calculate_leave_hours(self, employee):
        """حساب ساعات الإجازات (يوم كامل = 8 ساعات، ربع = 2 ساعة)"""
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
                _logger.info("Employee %s - Leave from %s to %s - Hours: %s", employee.name, start, end, hours)

        return total_hours

    def _calculate_assigned_hours(self, employee):
        """حساب الساعات المسندة من التايم شيت"""
        domain = [
            ('employee_id', '=', employee.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]

        # لو في مشروع محدد
        if self.project_id:
            domain.append(('project_id', '=', self.project_id.id))

        timesheets = self.env['account.analytic.line'].search(domain)
        assigned_total = sum(timesheets.mapped('unit_amount'))
        _logger.info("Employee %s - Assigned Hours from Timesheets: %s", employee.name, assigned_total)

        return assigned_total


class EmployeeWorkloadReportLine(models.Model):
    _name = 'employee.workload.report.line'
    _description = 'Employee Workload Report Line'
    _order = 'load_percentage desc, employee_id'

    report_id = fields.Many2one('employee.workload.report', string='Report', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    capacity_hours = fields.Float(string='Capacity Hours', digits=(10, 2))
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
