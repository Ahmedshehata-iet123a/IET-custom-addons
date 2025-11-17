from odoo import models, fields, api
from datetime import datetime
import base64
import io
import logging
import openpyxl

_logger = logging.getLogger(__name__)

class ProjectImportPlan(models.TransientModel):
    _name = 'project.import.plan'
    _description = 'Import Project Plan from Excel'

    excel_file = fields.Binary(string='Excel File', required=True)
    filename = fields.Char(string='Filename')
    project_id = fields.Many2one('project.project', string='Project', required=True,
                                 default=lambda self: self.env.context.get('default_project_id'))

    def action_import_plan(self):
        """استيراد خطة المشروع من ملف Excel (xlsx فقط)"""
        if not self.excel_file:
            raise UserWarning("Please upload an Excel file first!")

        try:
            # فك تشفير الملف
            file_content = base64.b64decode(self.excel_file)
            workbook = openpyxl.load_workbook(filename=io.BytesIO(file_content), data_only=True)
            sheet = workbook.active

            # البحث عن صف الهيدر (يبدأ بـ Task Name)
            header_row = None
            for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                if row and row[0] and 'Task Name' in str(row[0]):
                    header_row = row_idx
                    break

            if header_row is None:
                raise UserWarning("Cannot find header row with 'Task Name'")

            # قراءة البيانات
            plan_lines_to_create = []
            rows = list(sheet.iter_rows(values_only=True))[header_row + 1:]
            for row_idx, row in enumerate(rows, start=header_row + 1):
                try:
                    task_name = row[0]
                    if not task_name or str(task_name).strip() == '':
                        continue

                    # قراءة التواريخ
                    planned_start = self._parse_date(row[1])
                    actual_start = self._parse_date(row[2])
                    planned_end = self._parse_date(row[3])
                    actual_end = self._parse_date(row[4])

                    task_owner = row[5] if len(row) > 5 else ''
                    done = row[6] if len(row) > 6 else ''
                    comments = row[7] if len(row) > 7 else ''

                    # تحويل Done إلى boolean
                    status_done = str(done).strip().lower() in ['true', '1', 'yes', 'done', 'x']

                    vals = {
                        'project_id': self.project_id.id,
                        'name': str(task_name).strip(),
                        'planned_start_date': planned_start,
                        'actual_start_date': actual_start,
                        'planned_end_date': planned_end,
                        'actual_end_date': actual_end,
                        'task_owner': str(task_owner).strip() if task_owner else '',
                        'status_done': status_done,
                        'comments': str(comments).strip() if comments else '',
                    }

                    plan_lines_to_create.append(vals)

                except Exception as e:
                    _logger.warning(f"Error processing row {row_idx}: {str(e)}")
                    continue

            # إنشاء الخطوط الجديدة
            if plan_lines_to_create:
                self.env['project.plan.line'].create(plan_lines_to_create)
                _logger.info(f"Successfully imported {len(plan_lines_to_create)} plan lines")

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Successfully imported {len(plan_lines_to_create)} tasks',
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

        except Exception as e:
            _logger.error(f"Error importing project plan: {str(e)}")
            raise UserWarning(f"Error importing file: {str(e)}")

    def _parse_date(self, value):
        """تحويل التاريخ من Excel إلى Odoo datetime"""
        if not value:
            return False

        if isinstance(value, datetime):
            return value

        # محاولة تحويل النصوص
        date_str = str(value).strip()
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                    '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        _logger.warning(f"Cannot parse date: {value}")
        return False
