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
    project_ids = fields.Many2many('project.project', string='Projects')
    employee_id = fields.Many2one('hr.employee', string='Employee')
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
        """توليد تقرير الأحمال للموظفين مع تفاصيل المشاريع"""
        self.ensure_one()

        # حذف السطور القديمة
        self.line_ids.unlink()

        # 1. تحديد نطاق البحث عن التايم شيت
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('employee_id', '!=', False)
        ]

        # فلترة حسب الموظف
        if self.employee_id:
            domain.append(('employee_id', '=', self.employee_id.id))

        # فلترة حسب المشاريع (Many2many)
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))

        # جلب التايم شيت وتجميع البيانات
        timesheets = self.env['account.analytic.line'].search(domain)

        # هيكل البيانات: {employee_id: {project_id: hours, 'total_capacity': capacity}}
        data = {}

        # لضمان وجود الموظف حتى لو لم يكن لديه تايم شيت (في حالة الفلتر بدون مشروع أو فلتر بموظف محدد)
        target_employees = self.env['hr.employee']
        if self.employee_id:
            target_employees = self.employee_id
        elif not self.project_ids:
            # كل الموظفين النشطين في حالة عدم تحديد مشاريع
            target_employees = self.env['hr.employee'].search([('active', '=', True)])

        # تهيئة البيانات للموظفين المستهدفين
        for emp in target_employees:
            if emp.id not in data:
                # حساب السعة مرة واحدة للموظف
                capacity = self._calculate_capacity_hours(emp)
                data[emp.id] = {
                    'employee': emp,
                    'projects': {},
                    'capacity': capacity
                }

        # تجميع الساعات من التايم شيت
        for line in timesheets:
            emp = line.employee_id
            if emp.id not in data:
                # الموظف ظهر في التايم شيت ولم يكن في القائمة الأولية (مثلا عند الفلترة بمشروع)
                capacity = self._calculate_capacity_hours(emp)
                data[emp.id] = {
                    'employee': emp,
                    'projects': {},
                    'capacity': capacity
                }

            proj_id = line.project_id.id if line.project_id else False
            if proj_id not in data[emp.id]['projects']:
                data[emp.id]['projects'][proj_id] = 0
            data[emp.id]['projects'][proj_id] += line.unit_amount

        # إنشاء سطور التقرير
        for emp_id, emp_data in data.items():
            capacity = emp_data['capacity']
            projects = emp_data['projects']

            if not projects:
                # إذا لم يكن هناك مشاريع (0 ساعات)، ننشئ سطر واحد فارغ للموظف
                self._create_report_line(emp_data['employee'], False, capacity, 0)
            else:
                # سطر لكل مشروع
                for proj_id, hours in projects.items():
                    project = self.env['project.project'].browse(proj_id) if proj_id else False
                    self._create_report_line(emp_data['employee'], project, capacity, hours)

        return True

    def _create_report_line(self, employee, project, capacity, assigned_hours):
        load_percentage = (assigned_hours / capacity * 100) if capacity > 0 else 0

        if load_percentage >= 100:
            status = 'overload'
        elif load_percentage >= 80:
            status = 'normal'
        else:
            status = 'under'

        vals = {
            'report_id': self.id,
            'employee_id': employee.id,
            'project_id': project.id if project else False,
            'capacity_hours': capacity,
            'assigned_hours': assigned_hours,
            'load_percentage': load_percentage,
            'status': status,
        }

        # حساب بيانات المشروع
        if project and project.date_start:
            metrics = self._calculate_project_metrics(project)
            vals.update(metrics)

        self.env['employee.workload.report.line'].create(vals)

    def _calculate_project_metrics(self, project):
        """حساب مقاييس التحكم في الجدول الزمني للمشروع"""
        today = fields.Date.today()
        planned_duration = 0
        if project.date and project.date_start:
            # حساب أيام العمل بين تاريخ البداية والنهاية
            calendar = self.env.company.resource_calendar_id
            start_dt = datetime.combine(project.date_start, datetime.min.time())
            end_dt = datetime.combine(project.date, datetime.max.time())
            work_hours = calendar.get_work_hours_count(start_dt, end_dt, compute_leaves=False)
            planned_duration = work_hours / 8  # تحويل الساعات لأيام (8 ساعات = يوم عمل)

        days_passed = 0
        if project.date_start and project.date_start <= today:
            calendar = self.env.company.resource_calendar_id
            start_dt = datetime.combine(project.date_start, datetime.min.time())
            end_dt = datetime.combine(today, datetime.max.time())
            work_hours = calendar.get_work_hours_count(start_dt, end_dt, compute_leaves=False)
            days_passed = work_hours / 8

        expected_progress = 0
        if planned_duration > 0:
            expected_progress = (days_passed / planned_duration) * 100


        actual_progress = project.completion_percent if hasattr(project, 'completion_percent') else 0

        variation_percentage = (actual_progress - expected_progress)  # e.g. -10
        delay_days = (variation_percentage / 100.0) * planned_duration

        if delay_days >= 0:
            schedule_status = 'on_track'
        elif delay_days >= -5:
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

    def _calculate_capacity_hours(self, employee):
        """ساعات السعة = ساعات العمل - إجازات الموظف الشخصية مع تجاهل الجمعة والسبت"""
        calendar = employee.resource_calendar_id or self.env.company.resource_calendar_id

        total_hours = 0
        current_date = self.date_from
        while current_date <= self.date_to:
            if current_date.weekday() not in (4, 5):
                start_dt = datetime.combine(current_date, datetime.min.time())
                end_dt = datetime.combine(current_date, datetime.max.time())
                hours = calendar.get_work_hours_count(start_dt, end_dt, compute_leaves=False)
                total_hours += hours
            current_date += timedelta(days=1)

        leave_hours = self._calculate_leave_hours(employee)

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


class EmployeeWorkloadReportLine(models.Model):
    _name = 'employee.workload.report.line'
    _description = 'Employee Workload Report Line'
    _order = 'project_id, employee_id, load_percentage desc'

    report_id = fields.Many2one('employee.workload.report', string='Report', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    project_id = fields.Many2one('project.project', string='Project')
    project_stage_id = fields.Many2one('project.project.stage', string='Project Stage', related='project_id.stage_id', store=True)

    # Project Schedule Control Fields
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
