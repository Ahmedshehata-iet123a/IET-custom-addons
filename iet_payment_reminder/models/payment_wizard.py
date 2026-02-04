# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProjectPaymentWizard(models.TransientModel):
    _name = 'project.payment.wizard'
    _description = 'Project Payment Wizard'

    project_id = fields.Many2one('project.project', string='Project', readonly=True)
    payment_id = fields.Many2one('project.payment', string='Payments', readonly=True)
    customer_id = fields.Many2one(related='payment_id.customer_id', string='Customer')
    contract_payment_date = fields.Date(related='payment_id.contract_payment_date', string='Contract Payment Date')
    uat_due_payment = fields.Date(related='payment_id.uat_due_payment')
    live_due_payment = fields.Date(related='payment_id.live_due_payment')
    actual_contract_payment_date = fields.Date(related='payment_id.actual_contract_payment_date')
    actual_uat_due_payment = fields.Date(related='payment_id.actual_uat_due_payment')
    actual_live_due_payment = fields.Date(related='payment_id.actual_live_due_payment')
    notes = fields.Text(related='payment_id.notes')
    has_installments = fields.Boolean(related='payment_id.has_installments')
    installment_count = fields.Selection(related='payment_id.installment_count')
    installment_date_1 = fields.Date(related='payment_id.installment_date_1')
    installment_date_2 = fields.Date(related='payment_id.installment_date_2')
    installment_date_3 = fields.Date(related='payment_id.installment_date_3')
    installment_date_4 = fields.Date(related='payment_id.installment_date_4')
    actual_installment_date_1 = fields.Date(related='payment_id.actual_installment_date_1')
    actual_installment_date_2 = fields.Date(related='payment_id.actual_installment_date_2')
    actual_installment_date_3 = fields.Date(related='payment_id.actual_installment_date_3')
    actual_installment_date_4 = fields.Date(related='payment_id.actual_installment_date_4')
    contract_done = fields.Boolean(related='payment_id.contract_done')
    uat_done = fields.Boolean(related='payment_id.uat_done')
    live_done = fields.Boolean(related='payment_id.live_done')
