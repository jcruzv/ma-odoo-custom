from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    included_product_ids = fields.Many2many('product.template', string='Productos Incluidos')

    @api.onchange('product_id')
    def _onchange_product_id_included(self):
        if self.product_id and self.product_id.included_product_ids:
            self.included_product_ids = self.product_id.included_product_ids
