from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = 'project.project'

    ma_related_product_tmpl_ids = fields.Many2many(
        'product.template',
        compute='_compute_ma_related_product_tmpl_ids',
        inverse='_inverse_ma_related_product_tmpl_ids',
        string='Productos Relacionados'
    )

    def _compute_ma_related_product_tmpl_ids(self):
        for project in self:
            # servicios: campo nativo; bienes: campo MA
            project.ma_related_product_tmpl_ids = self.env['product.template'].search([
                '|',
                ('project_template_id', '=', project.id),
                ('ma_project_template_id', '=', project.id),
            ])

    def _inverse_ma_related_product_tmpl_ids(self):
        for project in self:
            # Productos que actualmente tienen este proyecto asignado en la base de datos
            old_products = self.env['product.template'].search([
                '|',
                ('project_template_id', '=', project.id),
                ('ma_project_template_id', '=', project.id),
            ])
            # Nuevos productos seleccionados en el campo
            new_products = project.ma_related_product_tmpl_ids

            # Productos a los que hay que quitarles este proyecto (fueron deseleccionados)
            for prod in old_products - new_products:
                prod.project_template_id = False
                prod.ma_project_template_id = False
                prod.ma_generate_project = False

            # Productos a los que hay que asignarles este proyecto (fueron seleccionados)
            for prod in new_products - old_products:
                if prod.type == 'service':
                    if prod.service_tracking == 'no':
                        prod.service_tracking = 'task_in_project'
                    prod.project_template_id = project.id
                else:
                    # los bienes no admiten service_tracking (Odoo lo fuerza a 'no')
                    prod.ma_generate_project = True
                    prod.ma_project_template_id = project.id
