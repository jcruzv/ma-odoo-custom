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
        # sale_project.write() fuerza service_tracking='no' y project_id=False
        # cuando el tipo pasa a no-servicio. No se puede evitar, pero sí
        # deshacer: primero se limpia la plantilla (con tracking 'no' la
        # constraint _check_project_and_template la prohíbe) y al final se
        # restaura todo junto, en un estado ya coherente.
        keep = {}
        if vals.get('type') and vals['type'] != 'service' and 'service_tracking' not in vals:
            for product in self:
                if product.service_tracking == 'no':
                    continue
                keep[product.id] = {
                    'service_tracking': product.service_tracking,
                    'project_id': product.project_id.id,
                    'project_template_id': product.project_template_id.id,
                }
            if keep:
                super(ProductTemplate, self.browse(list(keep))).write({
                    'project_id': False,
                    'project_template_id': False,
                })
        res = super().write(vals)
        for product_id, restore in keep.items():
            super(ProductTemplate, self.browse(product_id)).write(restore)
        return res
