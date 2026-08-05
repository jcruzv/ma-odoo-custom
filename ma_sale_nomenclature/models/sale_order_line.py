from odoo import _, api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _ma_lines_to_generate_project(self):
        """Líneas de bienes marcadas para generar proyecto.

        Los servicios los sigue manejando el core vía service_tracking, así que
        se excluyen aquí para no duplicar el proyecto.
        """
        return self.filtered(
            lambda sol: sol.product_id.ma_generate_project
            and not sol.is_service
            and not sol.project_id
            and not sol.is_expense
            and not (sol._is_line_optional() and sol.product_uom_qty == 0)
        )

    def _ma_generate_projects(self):
        """Crea (o reutiliza) un proyecto por orden + plantilla."""
        lines = self._ma_lines_to_generate_project()
        if not lines:
            return

        # Proyectos ya generados por la misma orden: evita duplicar si la orden se
        # canceló, se pasó a borrador y se volvió a confirmar.
        cache = {}
        done_lines = self.env['sale.order.line'].search([
            ('order_id', 'in', lines.order_id.ids),
            ('project_id', '!=', False),
        ])
        for sol in done_lines:
            if sol.product_id.ma_generate_project:
                key = (sol.order_id.id, sol.product_id.ma_project_template_id.id)
                cache.setdefault(key, sol.project_id)

        for line in lines.sorted(lambda sol: (sol.sequence, sol.id)):
            template = line.product_id.ma_project_template_id
            key = (line.order_id.id, template.id)
            project = cache.get(key)
            if not project:
                project = line._ma_create_project(template)
                cache[key] = project
            line.project_id = project
            if not line.order_id.project_id:
                line.order_id.project_id = project
            if line.product_id.ma_generate_task and not line.task_id:
                line._timesheet_create_task(project)

    def _ma_create_project(self, template):
        self.ensure_one()
        order = self.order_id
        account = order.project_account_id or self.env['account.analytic.account'].create(
            order._prepare_analytic_account_data()
        )
        # sale_line_id NO se puede ligar con una línea de bien: sale_timesheet
        # (project._check_sale_line_type) y sale_project (project.task) exigen
        # línea de servicio. El vínculo con la venta queda por
        # reinvoiced_sale_order_id en el proyecto, sale_order_id en las tareas y
        # project_id en la línea. Por lo mismo el proyecto no es facturable.
        values = {
            'name': self._ma_project_name(template),
            'account_id': account.id,
            'partner_id': order.partner_id.id,
            'company_id': self.company_id.id,
            'active': True,
            'allow_billable': False,
        }
        if template:
            if template.is_template:
                project = template.action_create_from_template(values)
            else:
                project = template.copy(values)
            project.tasks.write({'partner_id': order.partner_id.id})
        else:
            project = self.env['project.project'].create(values)

        # sin etapas las tareas caen en 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create([{
                'name': name,
                'fold': fold,
                'sequence': sequence,
            } for name, fold, sequence in [
                (_('To Do'), False, 5),
                (_('In Progress'), False, 10),
                (_('Done'), False, 15),
                (_('Cancelled'), True, 20),
            ]])

        self.project_id = project
        project.reinvoiced_sale_order_id = order
        return project

    def _ma_project_name(self, template):
        self.ensure_one()
        order = self.order_id
        name = '%s - %s' % (order.client_order_ref, order.name) if order.client_order_ref else order.name
        if template:
            return '%s - %s' % (name, template.name)
        product = self.product_id
        if product.default_code:
            return '%s - [%s] %s' % (name, product.default_code, product.name)
        return '%s - %s' % (name, product.name)

    def _ma_clean_task_vals(self, values):
        """Quita de los valores de tarea lo que Odoo prohíbe en líneas de bien."""
        values.pop('sale_line_id', None)
        # sale_order_id se recomputa a False sin sale_line_id + allow_billable
        values.pop('sale_order_id', None)
        return values

    def _timesheet_create_task_prepare_values(self, project):
        values = super()._timesheet_create_task_prepare_values(project)
        if not self.is_service and self.product_id.ma_generate_project:
            # horas asignadas = cantidad vendida no tiene sentido en un bien
            values['allocated_hours'] = 0.0
            self._ma_clean_task_vals(values)
        return values

    def _prepare_task_template_vals(self, template, project):
        values = super()._prepare_task_template_vals(template, project)
        if not self.is_service and self.product_id.ma_generate_project:
            values['allocated_hours'] = 0.0
            self._ma_clean_task_vals(values)
        return values

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # líneas agregadas a una orden ya confirmada
        confirmed = lines.filtered(lambda sol: sol.state == 'sale' and not sol.is_expense)
        if confirmed and not self.env.context.get('disable_project_task_generation'):
            confirmed.sudo()._ma_generate_projects()
        return lines
