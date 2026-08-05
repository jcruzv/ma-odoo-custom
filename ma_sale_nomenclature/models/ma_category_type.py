from odoo import models, fields

class MaCategoryType(models.Model):
    _name = 'ma.category.type'
    _description = 'Tipo de Servicio MA'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)
