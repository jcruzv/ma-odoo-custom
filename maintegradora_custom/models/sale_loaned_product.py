from odoo import models, fields

class SaleLoanedProduct(models.Model):
    _name = 'sale.loaned.product'
    _description = 'Productos Prestados'

    name = fields.Char(string='Descripción')
    active = fields.Boolean(string='Activo', default=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén')
    quantity = fields.Float(string='Cantidad')
    product_template_id = fields.Many2one('product.template', string='Producto')
    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta')
    sequence = fields.Integer(string='Secuencia', default=10)
