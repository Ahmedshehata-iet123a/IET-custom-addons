# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    employee_coach_id = fields.Many2one(
        'hr.employee',
        string="Employee Coach",
        related='employee_id.coach_id',
        store=True,
    )
