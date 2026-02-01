# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    # employee_coach_id field removed as we use direct traversal in record rule

