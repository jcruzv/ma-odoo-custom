from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Odoo solo permite generar proyecto desde productos de tipo servicio
    # (product._compute_service_tracking fuerza service_tracking='no' en bienes y
    # sale_project filtra por sale.order.line.is_service). Estos campos son
    # propios para no pelearse con esa lógica.
    ma_generate_project = fields.Boolean(
        string='Generar proyecto al confirmar',
        help="Al confirmar la orden de venta se crea un proyecto (y su tarea) "
             "para este producto, aunque sea un bien y no un servicio.",
    )
    ma_project_template_id = fields.Many2one(
        'project.project',
        string='Plantilla de proyecto',
        domain="[('is_template', '=', True)]",
        help="Plantilla desde la que se copia el proyecto. Vacío = proyecto en blanco.",
    )
    ma_generate_task = fields.Boolean(
        string='Generar tarea',
        default=True,
        help="Además del proyecto, crea una tarea ligada a la línea de venta.",
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    ma_generate_project = fields.Boolean(
        related='product_tmpl_id.ma_generate_project', readonly=False)
    ma_project_template_id = fields.Many2one(
        related='product_tmpl_id.ma_project_template_id', readonly=False)
    ma_generate_task = fields.Boolean(
        related='product_tmpl_id.ma_generate_task', readonly=False)
