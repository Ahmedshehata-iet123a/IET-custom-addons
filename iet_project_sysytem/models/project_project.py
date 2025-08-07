from odoo import models, fields
import xlsxwriter
import io
import base64
import logging

_logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = 'project.project'

    project_plan_line_ids = fields.One2many(
        'project.plan.line',
        'project_id',
        string='Project Plan Lines'
    )

    def action_generate_tasks(self):
        Task = self.env['project.task']
        for project in self:
            task_type_ids = self.env['project.task.type'].search([
                ('generate_tasks', '=', True),
                ('project_ids', 'in', [project.id])
            ])

            if not task_type_ids:
                _logger.warning("No task types found for project %s with generate_tasks=True", project.name)
                continue

            for plan_line in project.project_plan_line_ids.filtered(lambda l: not l.display_type):
                existing_task = Task.search([
                    ('project_id', '=', project.id),
                    ('name', '=', plan_line.name),
                ], limit=1)
                if not existing_task:
                    vals = {
                        'name': plan_line.name,
                        'project_id': project.id,
                        'date_start': plan_line.planned_start_date,
                        'end_date': plan_line.planned_end_date,
                        'stage_id': task_type_ids[0].id,
                    }
                    _logger.info("Creating task with vals: %s", vals)
                    Task.create(vals)

    def action_print_project_plan(self):
        for project in self:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet("Project Plan")

            header_format = workbook.add_format({'bold': True, 'bg_color': '#CFE2F3', 'border': 1})
            task_format = workbook.add_format({'border': 1})
            title_format = workbook.add_format({'bold': True, 'font_size': 14})
            date_format = workbook.add_format({'italic': True, 'align': 'right'})

            worksheet.set_column('A:H', 22)

            logo = project.company_id.logo
            if logo:
                image_data = io.BytesIO(base64.b64decode(logo))
                worksheet.insert_image('A1', 'logo.png', {
                    'image_data': image_data,
                    'x_scale': 0.5,
                    'y_scale': 0.5,
                    'x_offset': 0,
                    'y_offset': 0,
                    'object_position': 1
                })

            worksheet.merge_range('C1:D1', project.company_id.name or '', title_format)

            current_date = fields.Date.context_today(project)
            worksheet.merge_range('E1:F1', f'Date: {current_date.strftime("%Y-%m-%d")}', date_format)

            headers = ["Task Name", "Planned Start Date", "Actual Start Date",
                       "Planned End Date", "Actual End Date", "Task Owner", "Status", "Comments"]
            header_row = 3
            for col, header in enumerate(headers):
                worksheet.write(header_row, col, header, header_format)

            row = header_row + 1

            plan_lines = project.project_plan_line_ids
            for line in plan_lines:
                worksheet.write(row, 0, line.name or '', task_format)
                worksheet.write(row, 1, line.planned_start_date.strftime(
                    "%Y-%m-%d %H:%M") if line.planned_start_date else '', task_format)
                worksheet.write(row, 2, line.actual_start_date.strftime(
                    "%Y-%m-%d %H:%M") if line.actual_start_date else '', task_format)
                worksheet.write(row, 3, line.planned_end_date.strftime(
                    "%Y-%m-%d %H:%M") if line.planned_end_date else '', task_format)
                worksheet.write(row, 4, line.actual_end_date.strftime(
                    "%Y-%m-%d %H:%M") if line.actual_end_date else '', task_format)
                worksheet.write(row, 5, line.task_owner or '', task_format)
                worksheet.write(row, 6, line.status or '', task_format)
                worksheet.write(row, 7, line.comments or '', task_format)
                row += 1

            workbook.close()
            output.seek(0)

            attachment = self.env['ir.attachment'].create({
                'name': f'{project.name}_project_plan.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(output.read()),
                'res_model': self._name,
                'res_id': project.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })

            download_url = f'/web/content/{attachment.id}?download=true'
            return {
                'type': 'ir.actions.act_url',
                'url': download_url,
                'target': 'self',
            }
