# models/project_project_inherit.py
from odoo import models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    def unlink(self):
        for record in self:
             self.env['deleted.record.log'].sudo().create({
                'name': record.name or 'Unnamed Project',
                'model_name': 'project.project',
                'deleted_by_id': self.env.uid,
            })

        return super(ProjectProject, self).unlink()