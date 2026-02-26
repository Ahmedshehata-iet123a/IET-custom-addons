from odoo import models, fields

class DeletedRecordLog(models.Model):
    _name = 'deleted.record.log'
    _description = 'Deleted Record Log'
    _order = 'deleted_date desc'

    name = fields.Char(string="Record Name", required=True, readonly=True)
    model_name = fields.Char(string="Model Name", required=True, readonly=True)
    deleted_by_id = fields.Many2one('res.users', string="Deleted By", readonly=True)
    deleted_date = fields.Datetime(string="Deletion Date", default=fields.Datetime.now, readonly=True)