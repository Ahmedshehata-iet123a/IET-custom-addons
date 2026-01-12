# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestCoachAccess(TransactionCase):

    def setUp(self):
        super(TestCoachAccess, self).setUp()
        self.env.user.groups_id += self.env.ref('base.group_user')
        
        # Create Employees
        self.coach = self.env['hr.employee'].create({
            'name': 'Coach',
            'user_id': self.env['res.users'].create({
                'name': 'Coach User',
                'login': 'coach_user',
                'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
            }).id
        })
        
        self.employee = self.env['hr.employee'].create({
            'name': 'Employee',
            'coach_id': self.coach.id,
            'user_id': self.env['res.users'].create({
                'name': 'Employee User',
                'login': 'employee_user',
                'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
            }).id
        })
        
        self.other_employee = self.env['hr.employee'].create({
            'name': 'Other Employee',
            'user_id': self.env['res.users'].create({
                'name': 'Other Employee User',
                'login': 'other_employee_user',
                'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
            }).id
        })

        # Create Timesheet
        self.timesheet = self.env['account.analytic.line'].with_user(self.employee.user_id).create({
            'name': 'Test Timesheet',
            'project_id': self.env['project.project'].create({'name': 'Test Project'}).id,
            'unit_amount': 2.0,
        })

    def test_coach_can_see_employee_timesheet(self):
        """ Test that the coach can see their employee's timesheet """
        timesheet = self.timesheet.with_user(self.coach.user_id)
        self.assertTrue(timesheet.read(['name']), "Coach should be able to read employee's timesheet")

    def test_other_employee_cannot_see_timesheet(self):
        """ Test that another employee cannot see the timesheet """
        timesheet = self.timesheet.with_user(self.other_employee.user_id)
        # Search should not return the record
        search_res = self.env['account.analytic.line'].with_user(self.other_employee.user_id).search([('id', '=', self.timesheet.id)])
        self.assertFalse(search_res, "Other employee should not be able to find the timesheet")
        
        # Direct read should raise AccessError (or return empty if record rule filters it out, but usually search is safer check for rules)
        # Actually, if we try to browse and read, record rules apply.
        # If record rules prevent access, search returns empty.
        # If we browse explicitly, reading fields might raise AccessError or just filter.
        # Let's rely on search for "visibility".
