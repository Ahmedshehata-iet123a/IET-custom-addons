{
    'name': 'Employee Workload Reports',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Track employee workload and capacity with detailed reports',
    'description': """
        Employee Workload Reports
        =========================
        Comprehensive employee workload tracking and reporting system integrated with Project module.

        Key Features:
        -------------
        * **Capacity Calculation**: Automatically calculates employee capacity based on:
          - Working calendar/schedule
          - Leave deductions (full day = 8h, half day = 4h, quarter day = 2h)

        * **Assigned Hours Tracking**: 
          - Pulls data from timesheet entries
          - Can filter by specific project or view all projects

        * **Load Analysis**:
          - Calculates load percentage: (Assigned Hours / Capacity Hours) × 100
          - Automatic status assignment:
            • Under: < 80% (Orange)
            • Normal: 80-99% (Green)
            • Overload: ≥ 100% (Red)

        * **Reporting Views**:
          - Monthly workload reports
          - Tree view with color-coded status
          - Graph analysis (bar charts)
          - Pivot tables for deep analysis
          - Filter by department, job position, status

        * **Project Integration**:
          - Generate reports for specific projects
          - Or view company-wide workload
          - Located in Project menu for easy access

        Navigation:
        -----------
        Project → Employee Workload → Workload Reports
        Project → Employee Workload → Workload Analysis

        Usage:
        ------
        1. Go to Project → Employee Workload → Workload Reports
        2. Click Create
        3. Set date range (defaults to current month)
        4. Optionally select a project (leave empty for all projects)
        5. Click "Generate Report"
        6. View results with color-coded status indicators
        7. Use Analysis menu for graphs and pivot tables
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'project',
        'hr',
        'hr_holidays',
        'hr_timesheet',
        'iet_project_system',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'views/employee_workload_views.xml',
        'views/employee_per_project_views.xml',
        'views/planned_vs_actual_views.xml',
        'views/reports_menu.xml',
        'data/ir_cron.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}