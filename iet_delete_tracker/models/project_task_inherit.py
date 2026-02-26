from odoo import models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def unlink(self):
        for record in self:

            self.env['deleted.record.log'].sudo().create({
                'name': record.name or 'Unnamed Task',
                'model_name': 'project.task',
                'deleted_by_id': self.env.uid,
            })

        return super(ProjectTask, self).unlink()