from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ProjectPlannedActualReport(models.Model):
    _name = 'project.planned.actual.report'
    _description = 'Project Planned vs Actual Report'
    _order = 'create_date desc'

    name = fields.Char(string='Report Name', required=True)
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    project_ids = fields.Many2many('project.project', string='Projects')
    line_ids = fields.One2many('project.planned.actual.report.line', 'report_id', string='Report Lines')

    @api.model
    def default_get(self, fields_list):
        res = super(ProjectPlannedActualReport, self).default_get(fields_list)
        today = fields.Date.today()
        res.update({
            'name': 'Planned vs Actual Report - ' + today.strftime('%Y-%m-%d')
        })
        return res

    def action_generate_report(self):
        """توليد تقرير المخطط مقابل الفعلي"""
        self.ensure_one()

        # حذف السطور القديمة
        self.line_ids.unlink()

        # جلب المشاريع
        domain = []
        if self.project_ids:
            domain.append(('id', 'in', self.project_ids.ids))

        if self.date_from or self.date_to:
            if self.date_from:
                domain.append('|')
                domain.append(('date_start', '>=', self.date_from))
                domain.append(('date', '>=', self.date_from))
            if self.date_to:
                domain.append('|')
                domain.append(('date_start', '<=', self.date_to))
                domain.append(('date', '<=', self.date_to))

        projects = self.env['project.project'].search(domain)

        for project in projects:
            # التواريخ المخططة من البروجكت
            planned_start = project.date_start
            planned_end = project.date

            # التواريخ الفعلية من حقول البروجكت
            actual_start = project.start_project_date if hasattr(project, 'start_project_date') else None
            actual_end = project.end_project_date if hasattr(project, 'end_project_date') else None

            # حساب الفروقات في الأيام
            start_variance_days = 0
            end_variance_days = 0

            if planned_start and actual_start:
                start_variance_days = (actual_start - planned_start).days

            if planned_end and actual_end:
                end_variance_days = (actual_end - planned_end).days

            # حساب الساعات المخططة (Planned Hours)
            planned_hours = self._calculate_working_hours(planned_start, planned_end, project)

            # حساب الساعات الفعلية (Actual Hours)
            actual_hours = self._calculate_working_hours(actual_start, actual_end, project)

            # حساب الفرق في الساعات
            hours_variance = actual_hours - planned_hours

            # تحديد الحالة
            status = self._determine_status(
                start_variance_days,
                end_variance_days,
                planned_end,
                actual_end
            )

            # إنشاء سطر التقرير
            self.env['project.planned.actual.report.line'].create({
                'report_id': self.id,
                'project_id': project.id,
                'planned_start_date': planned_start,
                'planned_end_date': planned_end,
                'actual_start_date': actual_start,
                'actual_end_date': actual_end,
                'start_variance_days': start_variance_days,
                'end_variance_days': end_variance_days,
                'planned_hours': planned_hours,
                'actual_hours': actual_hours,
                'hours_variance': hours_variance,
                'status': status,
            })

        return True

    def _calculate_working_hours(self, start_date, end_date, project):
        """حساب الساعات = (عدد أيام العمل - الإجازات) × 8 ساعات"""
        if not start_date or not end_date:
            return 0.0

        # الحصول على التقويم
        calendar = self.env.company.resource_calendar_id

        # حساب أيام العمل بدون إجازات
        working_days = 0
        current_date = start_date

        while current_date <= end_date:
            # تجاهل الجمعة (4) والسبت (5)
            if current_date.weekday() not in (4, 5):
                # التحقق من عدم وجود إجازة رسمية
                if not self._is_public_holiday(current_date, calendar):
                    working_days += 1

            current_date += timedelta(days=1)

        # ضرب عدد الأيام في 8 ساعات
        total_hours = working_days * 8

        _logger.info("Date Range: %s to %s - Working Days: %s - Total Hours: %s",
                     start_date, end_date, working_days, total_hours)

        return total_hours

    def _is_public_holiday(self, check_date, calendar):
        """التحقق من وجود إجازة رسمية في التاريخ المحدد"""
        if not calendar:
            return False

        # البحث عن إجازات عامة في هذا التاريخ
        public_leaves = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('resource_id', '=', False),  # إجازة عامة وليست خاصة بموظف
            ('date_from', '<=', datetime.combine(check_date, datetime.max.time())),
            ('date_to', '>=', datetime.combine(check_date, datetime.min.time())),
        ])

        return bool(public_leaves)

    def _determine_status(self, start_var, end_var, planned_end, actual_end):
        """تحديد حالة المشروع"""
        today = fields.Date.today()

        # إذا كان المشروع متأخر في الانتهاء
        if planned_end and planned_end < today and (not actual_end or actual_end > planned_end):
            return 'delayed'

        # إذا كان المشروع منتهي في الوقت المحدد أو مبكر
        if actual_end and planned_end and actual_end <= planned_end:
            return 'on_time'

        # إذا كان هناك تأخير في البداية أو النهاية
        if start_var > 0 or end_var > 0:
            return 'delayed'

        # إذا كان المشروع متقدم
        if start_var < 0 or end_var < 0:
            return 'early'

        return 'on_track'


class ProjectPlannedActualReportLine(models.Model):
    _name = 'project.planned.actual.report.line'
    _description = 'Project Planned vs Actual Report Line'
    _order = 'end_variance_days desc, project_id'

    report_id = fields.Many2one('project.planned.actual.report', string='Report', required=True, ondelete='cascade')
    project_id = fields.Many2one('project.project', string='Project', required=True)

    # التواريخ المخططة (من date_start و date)
    planned_start_date = fields.Date(string='Planned Start')
    planned_end_date = fields.Date(string='Planned End')

    # التواريخ الفعلية (من start_project_date و end_project_date)
    actual_start_date = fields.Date(string='Actual Start')
    actual_end_date = fields.Date(string='Actual End')

    # الفروقات في الأيام
    start_variance_days = fields.Integer(string='Start Variance (Days)')
    end_variance_days = fields.Integer(string='End Variance (Days)')

    # الساعات
    planned_hours = fields.Float(string='Planned Hours', digits=(10, 2))
    actual_hours = fields.Float(string='Actual Hours', digits=(10, 2))
    hours_variance = fields.Float(string='Hours Variance', digits=(10, 2))

    # الحالة
    status = fields.Selection([
        ('on_track', 'On Track'),
        ('on_time', 'Completed On Time'),
        ('early', 'Early'),
        ('delayed', 'Delayed'),
    ], string='Status', required=True)

    # معلومات إضافية
    partner_id = fields.Many2one('res.partner', related='project_id.partner_id', string='Customer', store=True)
    user_id = fields.Many2one('res.users', related='project_id.user_id', string='Project Manager', store=True)

    # حقول محسوبة لعرض الفروقات بشكل أفضل
    start_variance_display = fields.Char(
        string="Start Variance",
        compute="_compute_variance_display"
    )
    end_variance_display = fields.Char(
        string="End Variance",
        compute="_compute_variance_display"
    )
    hours_variance_display = fields.Char(
        string="Hours Variance",
        compute="_compute_variance_display"
    )

    @api.depends('start_variance_days', 'end_variance_days', 'hours_variance')
    def _compute_variance_display(self):
        for rec in self:
            # عرض فرق البداية
            if rec.start_variance_days > 0:
                rec.start_variance_display = f"+{rec.start_variance_days} days (Late)"
            elif rec.start_variance_days < 0:
                rec.start_variance_display = f"{rec.start_variance_days} days (Early)"
            else:
                rec.start_variance_display = "On Time"

            # عرض فرق النهاية
            if rec.end_variance_days > 0:
                rec.end_variance_display = f"+{rec.end_variance_days} days (Late)"
            elif rec.end_variance_days < 0:
                rec.end_variance_display = f"{rec.end_variance_days} days (Early)"
            else:
                rec.end_variance_display = "On Time"

            # عرض فرق الساعات
            if rec.hours_variance > 0:
                rec.hours_variance_display = f"+{rec.hours_variance:.2f} hrs (Over)"
            elif rec.hours_variance < 0:
                rec.hours_variance_display = f"{rec.hours_variance:.2f} hrs (Under)"
            else:
                rec.hours_variance_display = "On Budget"