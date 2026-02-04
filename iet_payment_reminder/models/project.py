# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Project(models.Model):
    _inherit = 'project.project'
    
    users_number = fields.Integer(string="Number of Users")
    payment_count = fields.Integer(compute='_compute_payment_count', string="Payment Count")

    def _compute_payment_count(self):
        for project in self:
            project.payment_count = self.env['project.payment'].search_count([('project_id', '=', project.id)])

    def action_view_payments(self):
        self.ensure_one()
        payment = self.env['project.payment'].search([('project_id', '=', self.id)], limit=1)
        wizard = self.env['project.payment.wizard'].create({
            'project_id': self.id,
            'payment_id': payment.id if payment else False
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'res_model': 'project.payment.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'form',
        }
