from odoo import models, fields

class AppointmentType(models.Model):
    _inherit = 'appointment.type'

    related_sale_order_id = fields.Many2one('sale.order', string='Venta relacionada')
