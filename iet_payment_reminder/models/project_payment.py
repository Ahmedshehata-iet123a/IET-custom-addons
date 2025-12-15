# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError


class ProjectPayment(models.Model):
    _name = 'project.payment'
    _description = 'Project Payment Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_id'

    # -------------------- Fields --------------------
    project_id = fields.Many2one(
        'project.project', string='Project', required=True, tracking=True,
        ondelete='cascade'
    )
    customer_id = fields.Many2one(
        'res.partner', string='Customer',
        related='project_id.partner_id', store=True, readonly=True
    )
    contract_payment_date = fields.Date(string='Contract Payment', required=True, tracking=True)
    uat_due_payment = fields.Date(string='UAT Due Payment', required=True, tracking=True)
    live_due_payment = fields.Date(string='Live Due Payment', required=True, tracking=True)
    notes = fields.Text(string='Notes')

    # -------------------- Notification & Snooze --------------------
    contract_notification_sent = fields.Boolean(string='Contract Notified', default=False)
    contract_snoozed_until = fields.Date(string='Contract Snoozed Until')
    contract_snooze_count = fields.Integer(string='Contract Snooze Count', default=0)

    uat_notification_sent = fields.Boolean(string='UAT Notified', default=False)
    uat_snoozed_until = fields.Date(string='UAT Snoozed Until')
    uat_snooze_count = fields.Integer(string='UAT Snooze Count', default=0)

    live_notification_sent = fields.Boolean(string='Live Notified', default=False)
    live_snoozed_until = fields.Date(string='Live Snoozed Until')
    live_snooze_count = fields.Integer(string='Live Snooze Count', default=0)

    # -------------------- Done Checkboxes --------------------
    contract_done = fields.Boolean(string='Contract Done', default=False)
    uat_done = fields.Boolean(string='UAT Done', default=False)
    live_done = fields.Boolean(string='Live Done', default=False)
    contract_appear = fields.Boolean(default=False)
    uat_appear = fields.Boolean(default=False)
    live_appear = fields.Boolean(default=False)

    contract_done_date = fields.Datetime(string='Contract Done Date', readonly=True)
    uat_done_date = fields.Datetime(string='UAT Done Date', readonly=True)
    live_done_date = fields.Datetime(string='Live Done Date', readonly=True)

    # -------------------- State --------------------
    state = fields.Selection([
        ('pending', 'Draft'),
        ('snoozed_contract', 'Snoozed Contract'),
        ('snoozed_uat', 'Snoozed UAT'),
        ('snoozed_live', 'Snoozed Live'),
        ('completed', 'Completed'),
    ], string='Status', default='pending', tracking=True)

    # -------------------- Actions --------------------

    def action_contract_done(self):
        self.write({
            'contract_done': True,
            'contract_notification_sent': True,
            'contract_done_date': fields.Datetime.now(),
        })
        self._update_state()
        self.message_post(body="Contract <strong>Done</strong> ✅")
        return True

    def action_uat_done(self):
        self.write({
            'uat_done': True,
            'uat_notification_sent': True,
            'uat_done_date': fields.Datetime.now(),
        })
        self._update_state()
        self.message_post(body="UAT <strong>Done</strong> ✅")
        return True

    def action_live_done(self):
        self.write({
            'live_done': True,
            'live_notification_sent': True,
            'live_done_date': fields.Datetime.now(),
        })
        self._update_state()
        self.message_post(body="Live <strong>Done</strong> ✅")
        return True

    def _update_state(self):
        """تحديث الـ state حسب أي نوع تم عمل Done أو Snooze"""
        if self.contract_snoozed_until and not self.contract_done:
            self.state = 'snoozed_contract'
        elif self.uat_snoozed_until and not self.uat_done:
            self.state = 'snoozed_uat'
        elif self.live_snoozed_until and not self.live_done:
            self.state = 'snoozed_live'
        elif self.contract_done and self.uat_done and self.live_done:
            self.state = 'completed'
        else:
            self.state = 'pending'

    def action_snooze_contract(self):
        if self.contract_snooze_count >= 2:
            raise UserError("Cannot snooze Contract more than 2 times.")
        snooze_date = fields.Date.today() + timedelta(days=3)
        self.write({
            'contract_snoozed_until': snooze_date,
            'contract_notification_sent': False,
            'contract_snooze_count': self.contract_snooze_count + 1,
        })
        self._update_state()
        self.message_post(
            body=f"Contract snoozed until <strong>{snooze_date}</strong> (#{self.contract_snooze_count}/2).")
        return True

    def action_snooze_uat(self):
        if self.uat_snooze_count >= 2:
            raise UserError("Cannot snooze UAT more than 2 times.")
        snooze_date = fields.Date.today() + timedelta(days=3)
        self.write({
            'uat_snoozed_until': snooze_date,
            'uat_notification_sent': False,
            'contract_appear': True,
            'uat_snooze_count': self.uat_snooze_count + 1,
        })
        self._update_state()
        self.message_post(body=f"UAT snoozed until <strong>{snooze_date}</strong> (#{self.uat_snooze_count}/2).")
        return True

    def action_snooze_live(self):
        if self.live_snooze_count >= 2:
            raise UserError("Cannot snooze Live more than 2 times.")
        snooze_date = fields.Date.today() + timedelta(days=3)
        self.write({
            'live_snoozed_until': snooze_date,
            'live_notification_sent': False,
            'live_snooze_count': self.live_snooze_count + 1,
        })
        self._update_state()
        self.message_post(body=f"Live snoozed until <strong>{snooze_date}</strong> (#{self.live_snooze_count}/2).")
        return True

    def action_back_to_pending(self):
        self.write({
            'contract_snoozed_until': False,
            'uat_snoozed_until': False,
            'live_snoozed_until': False,
            'contract_done': False,
            'uat_done': False,
            'live_done': False,
            'contract_notification_sent': False,
            'uat_notification_sent': False,
            'live_notification_sent': False,
        })
        self._update_state()
        self.message_post(body="Returned to <strong>Pending</strong>.")
        return True

    # ==================== Cron Job ====================

    @api.model
    def _send_payment_notifications(self):
        today = fields.Date.today()
        one_week_later = today + timedelta(days=7)
        one_day_before = today + timedelta(days=1)

        records = self.search([
            '|', '|',
            ('contract_payment_date', '<=', one_week_later),
            ('uat_due_payment', '<=', one_week_later),
            ('live_due_payment', '<=', one_week_later),
            ('state', '!=', 'completed')
        ])

        for payment in records:
            # --- Contract ---
            if (payment.contract_payment_date <= one_week_later
                    and not payment.contract_notification_sent
                    and payment.state in ['pending', 'snoozed']
                    and (not payment.contract_snoozed_until or payment.contract_snoozed_until <= today)):
                self._send_notification(payment, 'Contract', payment.contract_payment_date)
                payment.write({'contract_notification_sent': True, 'state': 'pending'})

            if (payment.contract_payment_date == one_day_before and payment.state != 'completed'):
                self._send_final_notification(payment, 'Contract', payment.contract_payment_date)

            # --- UAT ---
            if (payment.uat_due_payment <= one_week_later
                    and not payment.uat_notification_sent
                    and payment.state in ['pending', 'snoozed']
                    and (not payment.uat_snoozed_until or payment.uat_snoozed_until <= today)):
                self._send_notification(payment, 'UAT', payment.uat_due_payment)
                payment.write({'uat_notification_sent': True, 'state': 'pending'})

            if (payment.uat_due_payment == one_day_before and payment.state != 'completed'):
                self._send_final_notification(payment, 'UAT', payment.uat_due_payment)

            # --- Live ---
            if (payment.live_due_payment <= one_week_later
                    and not payment.live_notification_sent
                    and payment.state in ['pending', 'snoozed']
                    and (not payment.live_snoozed_until or payment.live_snoozed_until <= today)):
                self._send_notification(payment, 'Live', payment.live_due_payment)
                payment.write({'live_notification_sent': True, 'state': 'pending'})

            if (payment.live_due_payment == one_day_before and payment.state != 'completed'):
                self._send_final_notification(payment, 'Live', payment.live_due_payment)

    # ==================== Notifications ====================

    def _send_notification(self, payment, payment_type, payment_date):
        self._send_reminder(payment, payment_type, payment_date, is_final=False)

    def _send_final_notification(self, payment, payment_type, payment_date):
        self._send_reminder(payment, payment_type, payment_date, is_final=True)

    def _send_reminder(self, payment, payment_type, payment_date, is_final=False):
        project = payment.project_id
        manager = project.user_id
        customer = payment.customer_id

        partners = set()
        if manager and manager.partner_id:
            partners.add(manager.partner_id.id)
        if customer:
            partners.add(customer.id)

        if not partners:
            return

        days_left = (payment_date - fields.Date.today()).days
        if is_final:
            subject = f"FINAL REMINDER: {project.name} - {payment_type} Due TOMORROW"
            summary = f"FINAL: {payment_type} Due TOMORROW"
            body_html = f"""
            <p style="color: red; font-weight: bold;">URGENT: FINAL REMINDER</p>
            <p>The <strong>{payment_type}</strong> payment for project <strong>{project.name}</strong> 
            is due <strong>TOMORROW</strong> on <strong>{payment_date}</strong>.</p>
            <ul>
                <li><strong>Project:</strong> {project.name}</li>
                <li><strong>Customer:</strong> {customer.name if customer else 'N/A'}</li>
                <li><strong>Type:</strong> {payment_type}</li>
                <li><strong>Due Date:</strong> {payment_date}</li>
            </ul>
            <p style="color: red;"><strong>Act immediately.</strong></p>
            """
        else:
            subject = f"Reminder: {project.name} - {payment_type} Due in {days_left} Day(s)"
            summary = f"{payment_type} Due in {days_left} days"
            body_html = f"""
            <p>The <strong>{payment_type}</strong> payment for project <strong>{project.name}</strong> 
            is due in <strong>{days_left} day(s)</strong> on <strong>{payment_date}</strong>.</p>
            <ul>
                <li><strong>Project:</strong> {project.name}</li>
                <li><strong>Customer:</strong> {customer.name if customer else 'N/A'}</li>
                <li><strong>Type:</strong> {payment_type}</li>
                <li><strong>Due Date:</strong> {payment_date}</li>
            </ul>
            <p>Please take action.</p>
            """

        # Send Email
        self.env['mail.mail'].sudo().create({
            'subject': subject,
            'body_html': body_html,
            'email_from': self.env.company.email or 'no-reply@yourcompany.com',
            'recipient_ids': [(6, 0, list(partners))],
        }).send()

        # Schedule Activity
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        for partner_id in partners:
            payment.activity_schedule(
                activity_type_id=activity_type.id,
                summary=summary,
                note=body_html,
                date_deadline=payment_date,
                user_id=manager.id if manager else self.env.uid,
            )

        # Post in Chatter
        payment.message_post(
            body=body_html,
            subject=subject,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
