from odoo import models

# service_tracking que generan proyecto
PROJECT_TRACKING = ('project_only', 'task_in_project')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _ma_wants_project(self):
        self.ensure_one()
        return (
            self.product_id.service_tracking in PROJECT_TRACKING
            and not self.is_expense
            and not (self._is_line_optional() and self.product_uom_qty == 0)
        )

    def _timesheet_service_generation(self):
        """Un proyecto por cada línea de servicio, uno solo para todos los bienes.

        El core reutiliza un proyecto por (orden, plantilla) en los servicios y no
        genera nada en bienes, porque filtra por sale.order.line.is_service.
        """
        services = self.filtered(lambda sol: sol.is_service and sol._ma_wants_project())
        goods = self.filtered(lambda sol: not sol.is_service and sol._ma_wants_project())
        goods_global = self.filtered(
            lambda sol: not sol.is_service
            and sol.product_id.service_tracking == 'task_global_project'
            and not sol.is_expense
        )

        # el resto (servicios con proyecto global, líneas sin tracking) al core
        super(SaleOrderLine, self - services - goods - goods_global)._timesheet_service_generation()

        services._ma_generate_project_per_line()
        goods._ma_generate_goods_project()
        goods_global._ma_generate_goods_global_task()

    def _ma_generate_project_per_line(self):
        """Servicios: un proyecto propio por línea, aunque compartan plantilla."""
        accounts = {}
        for line in self.sorted(lambda sol: (sol.sequence, sol.id)):
            if line.project_id:
                continue
            account = accounts.get(line.order_id.id) or line._ma_project_account()
            accounts[line.order_id.id] = account
            project = line.with_context(project_account_id=account.id)._timesheet_create_project()
            if not line.order_id.project_id:
                line.order_id.project_id = project
            if line.product_id.service_tracking == 'task_in_project' and not line.task_id:
                line._timesheet_create_task(project=project)
            line._handle_milestones(project)

    def _ma_generate_goods_project(self):
        """Bienes: un único proyecto por orden, compartido por todas las líneas."""
        for order, lines in self.grouped('order_id').items():
            siblings = order.order_line.filtered(
                lambda sol: not sol.is_service and sol._ma_wants_project()
            )
            project = siblings.project_id[:1]
            lines = lines.sorted(lambda sol: (sol.sequence, sol.id))
            if not project:
                project = lines[0]._ma_create_project()
            for line in lines:
                if not line.project_id:
                    line.project_id = project
                if line.product_id.service_tracking == 'task_in_project' and not line.task_id:
                    line._timesheet_create_task(project=project)

    def _ma_generate_goods_global_task(self):
        """Bienes con 'Tarea' (proyecto global): solo la tarea, sin crear proyecto."""
        for line in self:
            if line.task_id or line.product_uom_qty <= 0:
                continue
            project = line.product_id.with_company(line.company_id).project_id or line.order_id.project_id
            if project:
                line._timesheet_create_task(project=project)

    def _ma_project_account(self):
        self.ensure_one()
        order = self.order_id
        return order.project_account_id or self.env['account.analytic.account'].create(
            order._prepare_analytic_account_data()
        )

    def _ma_create_project(self):
        self.ensure_one()
        order = self.order_id
        template = self.product_id.project_template_id
        # sale_line_id NO se puede ligar a una línea de bien: sale_timesheet
        # (project._check_sale_line_type) y sale_project (project.task) exigen
        # línea de servicio. El vínculo con la venta queda por
        # reinvoiced_sale_order_id y por project_id en la línea. Por lo mismo el
        # proyecto no es facturable: con allow_billable sale_timesheet le
        # asignaría a las tareas la última SOL de servicio del cliente.
        values = {
            'name': self._ma_project_name(template),
            'account_id': self._ma_project_account().id,
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
                ('Por hacer', False, 5),
                ('En progreso', False, 10),
                ('Hecho', False, 15),
                ('Cancelado', True, 20),
            ]])

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
        # horas asignadas = cantidad vendida no tiene sentido en un bien
        values['allocated_hours'] = 0.0
        return values

    def _timesheet_create_task_prepare_values(self, project):
        values = super()._timesheet_create_task_prepare_values(project)
        if not self.is_service and self.product_id.service_tracking != 'no':
            self._ma_clean_task_vals(values)
        return values

    def _prepare_task_template_vals(self, template, project):
        values = super()._prepare_task_template_vals(template, project)
        if not self.is_service and self.product_id.service_tracking != 'no':
            self._ma_clean_task_vals(values)
        return values
