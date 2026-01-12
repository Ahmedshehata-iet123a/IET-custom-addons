#!/usr/bin/env python3
"""
Script to verify Coach access to employee timesheets.
Run this from Odoo shell: odoo-bin shell -d odoo18.0
"""

# Get the environment
env = globals().get('env')
if not env:
    print("This script should be run from Odoo shell")
    exit(1)

# Create or get test users
def get_or_create_user(login, name, groups):
    user = env['res.users'].search([('login', '=', login)], limit=1)
    if not user:
        user = env['res.users'].create({
            'name': name,
            'login': login,
            'password': 'test123',
            'groups_id': [(6, 0, groups)]
        })
    return user

# Get required groups
timesheet_user_group = env.ref('hr_timesheet.group_hr_timesheet_user')
base_user_group = env.ref('base.group_user')

# Create Coach user
coach_user = get_or_create_user(
    'coach_test',
    'Coach Test User',
    [timesheet_user_group.id, base_user_group.id]
)

# Create Employee user
employee_user = get_or_create_user(
    'employee_test',
    'Employee Test User',
    [timesheet_user_group.id, base_user_group.id]
)

# Create employees
coach_emp = env['hr.employee'].search([('user_id', '=', coach_user.id)], limit=1)
if not coach_emp:
    coach_emp = env['hr.employee'].create({
        'name': 'Coach Employee',
        'user_id': coach_user.id,
    })

employee_emp = env['hr.employee'].search([('user_id', '=', employee_user.id)], limit=1)
if not employee_emp:
    employee_emp = env['hr.employee'].create({
        'name': 'Test Employee',
        'user_id': employee_user.id,
        'coach_id': coach_emp.id,  # Set coach
    })
else:
    employee_emp.coach_id = coach_emp.id

# Create a project
project = env['project.project'].search([('name', '=', 'Test Project Coach')], limit=1)
if not project:
    project = env['project.project'].create({
        'name': 'Test Project Coach',
    })

# Create timesheet as employee
timesheet = env['account.analytic.line'].with_user(employee_user).create({
    'name': 'Test Timesheet Entry',
    'project_id': project.id,
    'unit_amount': 5.0,
})

print(f"\n{'='*60}")
print("VERIFICATION RESULTS")
print(f"{'='*60}\n")

print(f"1. Created/Found Coach: {coach_emp.name} (User: {coach_user.login})")
print(f"2. Created/Found Employee: {employee_emp.name} (User: {employee_user.login})")
print(f"3. Employee's Coach: {employee_emp.coach_id.name if employee_emp.coach_id else 'None'}")
print(f"4. Created Timesheet ID: {timesheet.id}")
print(f"5. Timesheet employee_coach_id: {timesheet.employee_coach_id.name if timesheet.employee_coach_id else 'None'}")

# Test Coach access
print(f"\n{'='*60}")
print("ACCESS TEST")
print(f"{'='*60}\n")

# Check if coach can see the timesheet
coach_timesheets = env['account.analytic.line'].with_user(coach_user).search([
    ('id', '=', timesheet.id)
])

if coach_timesheets:
    print(f"✓ SUCCESS: Coach CAN see employee's timesheet (ID: {timesheet.id})")
else:
    print(f"✗ FAILED: Coach CANNOT see employee's timesheet (ID: {timesheet.id})")

# Check if employee can see their own timesheet
employee_timesheets = env['account.analytic.line'].with_user(employee_user).search([
    ('id', '=', timesheet.id)
])

if employee_timesheets:
    print(f"✓ SUCCESS: Employee CAN see their own timesheet")
else:
    print(f"✗ FAILED: Employee CANNOT see their own timesheet")

print(f"\n{'='*60}\n")

# Show the record rule
rule = env.ref('iet_coach_timesheet_access.rule_timesheet_coach_access')
print(f"Record Rule: {rule.name}")
print(f"Groups: {', '.join(rule.groups.mapped('name'))}")
print(f"Domain: {rule.domain_force}")
print(f"\n{'='*60}\n")
