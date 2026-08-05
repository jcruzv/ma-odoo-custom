from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # 'type' se quita A PROPÓSITO de las dependencias: el core
    # (product._compute_service_tracking) fuerza service_tracking='no' en todo lo
    # que no sea servicio, y aquí los bienes también deben generar proyecto.
    @api.depends('sale_ok')
    def _compute_service_tracking(self):
        for product in self:
            if not product.sale_ok:
                product.service_tracking = 'no'
            else:
                product.service_tracking = product.service_tracking or 'no'

    def write(self, vals):
        # sale_project.write() resetea service_tracking y project_id cuando el
        # tipo pasa a no-servicio; se restaura lo que estaba configurado.
        keep = {}
        if vals.get('type') and vals['type'] != 'service' and 'service_tracking' not in vals:
            for product in self:
                if product.service_tracking == 'no':
                    continue
                restore = {'service_tracking': product.service_tracking}
                if product.service_tracking == 'task_global_project':
                    restore['project_id'] = product.project_id.id
                keep[product.id] = restore
        res = super().write(vals)
        for product_id, restore in keep.items():
            super(ProductTemplate, self.browse(product_id)).write(restore)
        return res
