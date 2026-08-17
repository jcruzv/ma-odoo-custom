from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ma_portal_request = fields.Boolean(
        string='Solicitada desde el portal',
        default=False,
        copy=False,
        help="Marca las solicitudes de cotización creadas por empleados desde el portal.",
    )
