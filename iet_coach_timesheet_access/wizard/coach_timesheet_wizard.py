from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class CoachTimesheetWizard(models.TransientModel):
    _name = 'coach.timesheet.wizard'
    _description = 'Coach Timesheet Wizard'

    search_by = fields.Selection([
        ('employee', 'Search by Employee'),
        ('user', 'Search by User'),
        ('both', 'Search by Both')
    ], string='Search Method', default='both', required=True)

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        domain="[('coach_id', '=', current_coach_id)]"
    )
    current_coach_id = fields.Many2one(
        'hr.employee',
        string='Current Coach',
        default=lambda self: self.env.user.employee_id.id
    )
    date_from = fields.Date(
        string='From Date',
        required=True,
        default=lambda self: fields.Date.today() - timedelta(days=30)
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=fields.Date.today
    )
    timesheet_ids = fields.Many2many(
        'account.analytic.line',
        string='Timesheets',
        compute='_compute_timesheets'
    )
    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_timesheets'
    )
    debug_info = fields.Text(
        string='Debug Info',
        compute='_compute_debug_info'
    )

    @api.depends('employee_id')
    def _compute_debug_info(self):
        for wizard in self:
            if wizard.employee_id:
                employee = wizard.employee_id

                # البحث بالـ employee_id
                by_employee = self.env['account.analytic.line'].sudo().search([
                    ('employee_id', '=', employee.id)
                ])
                by_employee_visible = self.env['account.analytic.line'].search([
                    ('employee_id', '=', employee.id)
                ])

                # البحث بالـ user_id
                by_user = self.env['account.analytic.line'].search([
                    ('user_id', '=', employee.user_id.id)
                ]) if employee.user_id else self.env['account.analytic.line']

                # عينة من كل التايم شيت
                all_timesheets = self.env['account.analytic.line'].search([
                    ('employee_id', '!=', False)
                ], limit=10)

                info = f"""
=== Employee Info ===
Name: {employee.name}
ID: {employee.id}
User: {employee.user_id.name if employee.user_id else 'No User'}
User ID: {employee.user_id.id if employee.user_id else 'N/A'}

=== Timesheets by employee_id (ID={employee.id}) ===
Found (System): {len(by_employee)} entries
Found (Visible): {len(by_employee_visible)} entries
{chr(10).join([f"- Date: {t.date}, Hours: {t.unit_amount}, Project: {t.project_id.name if t.project_id else 'None'}, User: {t.user_id.name if t.user_id else 'N/A'}" for t in by_employee[:5]]) or 'No entries found'}

=== Timesheets by user_id (ID={employee.user_id.id if employee.user_id else 'N/A'}) ===
Found: {len(by_user)} entries
{chr(10).join([f"- Date: {t.date}, Hours: {t.unit_amount}, Project: {t.project_id.name if t.project_id else 'None'}, Employee: {t.employee_id.name if t.employee_id else 'N/A'}" for t in by_user[:5]]) or 'No entries found'}

=== Sample of ALL timesheets in system ===
{chr(10).join([f"- Employee: {t.employee_id.name if t.employee_id else 'None'} (ID: {t.employee_id.id if t.employee_id else 'N/A'}), User: {t.user_id.name if t.user_id else 'None'} (ID: {t.user_id.id if t.user_id else 'N/A'}), Date: {t.date}" for t in all_timesheets[:10]])}
                """
                wizard.debug_info = info
            else:
                wizard.debug_info = "Please select an employee first"

    @api.depends('employee_id', 'date_from', 'date_to', 'search_by')
    def _compute_timesheets(self):
        for wizard in self:
            if wizard.employee_id and wizard.date_from and wizard.date_to:
                employee = wizard.employee_id

                # بناء الـ domain حسب طريقة البحث
                if wizard.search_by == 'employee':
                    domain = [
                        ('employee_id', '=', employee.id),
                        ('date', '>=', wizard.date_from),
                        ('date', '<=', wizard.date_to),
                    ]
                elif wizard.search_by == 'user' and employee.user_id:
                    domain = [
                        ('user_id', '=', employee.user_id.id),
                        ('date', '>=', wizard.date_from),
                        ('date', '<=', wizard.date_to),
                    ]
                else:  # both
                    if employee.user_id:
                        domain = [
                            '|',
                            ('employee_id', '=', employee.id),
                            ('user_id', '=', employee.user_id.id),
                            ('date', '>=', wizard.date_from),
                            ('date', '<=', wizard.date_to),
                        ]
                    else:
                        domain = [
                            ('employee_id', '=', employee.id),
                            ('date', '>=', wizard.date_from),
                            ('date', '<=', wizard.date_to),
                        ]

                timesheets = self.env['account.analytic.line'].search(domain)

                _logger.info(f"Search by: {wizard.search_by}")
                _logger.info(f"Found {len(timesheets)} timesheet entries for {employee.name}")
                _logger.info(f"Date range: {wizard.date_from} to {wizard.date_to}")

                wizard.timesheet_ids = timesheets
                wizard.total_hours = sum(timesheets.mapped('unit_amount'))
            else:
                wizard.timesheet_ids = False
                wizard.total_hours = 0.0

    def action_view_timesheets(self):
        self.ensure_one()

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        # بناء الـ domain حسب طريقة البحث
        if self.search_by == 'employee':
            domain = [
                ('employee_id', '=', employee.id),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
            ]
        elif self.search_by == 'user' and employee.user_id:
            domain = [
                ('user_id', '=', employee.user_id.id),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
            ]
        else:  # both
            if employee.user_id:
                domain = [
                    '|',
                    ('employee_id', '=', employee.id),
                    ('user_id', '=', employee.user_id.id),
                    ('date', '>=', date_from),
                    ('date', '<=', date_to),
                ]
            else:
                domain = [
                    ('employee_id', '=', employee.id),
                    ('date', '>=', date_from),
                    ('date', '<=', date_to),
                ]

        count = self.env['account.analytic.line'].search_count(domain)
        _logger.info(f"Opening timesheets - Found {count} entries")
        _logger.info(f"Domain: {domain}")

        return {
            'name': f'Timesheets - {employee.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_employee_id': employee.id,
                'default_user_id': employee.user_id.id if employee.user_id else False,
            }
        }

    def action_check_employee_user_link(self):
        """زرار للتحقق من ربط الموظف بالـ User"""
        self.ensure_one()
        employee = self.employee_id

        message = f"""
Employee: {employee.name} (ID: {employee.id})
Linked User: {employee.user_id.name if employee.user_id else 'NOT LINKED'}
User ID: {employee.user_id.id if employee.user_id else 'N/A'}

Timesheets by employee_id: {self.env['account.analytic.line'].search_count([('employee_id', '=', employee.id)])}
Timesheets by user_id: {self.env['account.analytic.line'].search_count([('user_id', '=', employee.user_id.id)]) if employee.user_id else 0}
        """

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Employee-User Check',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }