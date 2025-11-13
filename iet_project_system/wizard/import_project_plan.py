from odoo import models, fields, api
from datetime import datetime
import xlrd
import base64
import io
import logging

_logger = logging.getLogger(__name__)


class ProjectImportPlan(models.TransientModel):
    _name = 'project.import.plan'
    _description = 'Import Project Plan from Excel'

    excel_file = fields.Binary(string='Excel File', required=True)
    filename = fields.Char(string='Filename')
    project_id = fields.Many2one('project.project', string='Project', required=True,
                                 default=lambda self: self.env.context.get('default_project_id'))

    def action_import_plan(self):
        """استيراد خطة المشروع من ملف Excel"""
        if not self.excel_file:
            raise UserWarning("Please upload an Excel file first!")

        try:
            # فك تشفير الملف
            file_content = base64.b64decode(self.excel_file)
            workbook = xlrd.open_workbook(file_contents=file_content)
            sheet = workbook.sheet_by_index(0)

            # البحث عن صف الهيدر (يبدأ بـ Task Name)
            header_row = None
            for row_idx in range(sheet.nrows):
                cell_value = sheet.cell_value(row_idx, 0)
                if cell_value and 'Task Name' in str(cell_value):
                    header_row = row_idx
                    break

            if header_row is None:
                raise UserWarning("Cannot find header row with 'Task Name'")

            # قراءة البيانات
            plan_lines_to_create = []
            for row_idx in range(header_row + 1, sheet.nrows):
                try:
                    task_name = sheet.cell_value(row_idx, 0)
                    if not task_name or task_name.strip() == '':
                        continue

                    # قراءة التواريخ
                    planned_start = self._parse_date(sheet, row_idx, 1)
                    actual_start = self._parse_date(sheet, row_idx, 2)
                    planned_end = self._parse_date(sheet, row_idx, 3)
                    actual_end = self._parse_date(sheet, row_idx, 4)

                    # قراءة باقي البيانات
                    task_owner = sheet.cell_value(row_idx, 5) if row_idx < sheet.nrows and sheet.ncols > 5 else ''
                    done = sheet.cell_value(row_idx, 6) if row_idx < sheet.nrows and sheet.ncols > 6 else ''
                    comments = sheet.cell_value(row_idx, 7) if row_idx < sheet.nrows and sheet.ncols > 7 else ''

                    # تحويل Done إلى boolean
                    status_done = False
                    if done:
                        done_str = str(done).strip().lower()
                        status_done = done_str in ['true', '1', 'yes', 'done', 'x']

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

            # حذف الخطوط القديمة (اختياري - يمكنك تعديل هذا السلوك)
            # self.project_id.project_plan_line_ids.unlink()

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
                    'next': {'type': 'ir.actions.act_window_close'},  # ← دي اللي بتقفل الويزرد بعد الإشعار
                }
            }

        except Exception as e:
            _logger.error(f"Error importing project plan: {str(e)}")
            raise UserWarning(f"Error importing file: {str(e)}")

    def _parse_date(self, sheet, row, col):
        """تحويل التاريخ من Excel إلى Odoo datetime"""
        try:
            cell_value = sheet.cell_value(row, col)
            if not cell_value or str(cell_value).strip() == '':
                return False

            cell_type = sheet.cell_type(row, col)

            # إذا كان التاريخ من نوع date في Excel
            if cell_type == 3:  # XL_CELL_DATE
                date_tuple = xlrd.xldate_as_tuple(cell_value, sheet.book.datemode)
                return datetime(*date_tuple)

            # إذا كان نص
            elif cell_type == 1:  # XL_CELL_TEXT
                date_str = str(cell_value).strip()
                # محاولة تحويل صيغ مختلفة
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                            '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue

            return False
        except Exception as e:
            _logger.warning(f"Error parsing date at row {row}, col {col}: {str(e)}")
            return False

