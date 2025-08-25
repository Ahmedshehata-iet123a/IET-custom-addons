from odoo import models,fields,api,_



class Project(models.Model):
    _inherit = 'project.project'

    image_128 = fields.Image("Image", max_width=128, max_height=128)

