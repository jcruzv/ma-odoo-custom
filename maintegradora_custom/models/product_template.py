from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    included_product_ids = fields.Many2many('product.template', 'product_template_included_rel', 'product_id', 'included_id', string='Productos Incluidos')

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    included_product_ids = fields.Many2many(related='product_tmpl_id.included_product_ids', readonly=False)
