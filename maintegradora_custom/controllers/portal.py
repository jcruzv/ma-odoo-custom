from odoo import _
from odoo.exceptions import AccessError
from odoo.http import request, route
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.project.controllers.portal import ProjectCustomerPortal


class MaProjectPortal(ProjectCustomerPortal):

    def _prepare_searchbar_sortings(self):
        sortings = super()._prepare_searchbar_sortings()
        # task_count es calculado sin store: no sirve para ordenar
        sortings.update({
            'status': {'label': _('Estado'), 'order': 'last_update_status'},
        })
        return sortings


class MaPurchaseRequestPortal(CustomerPortal):
    """Solicitudes de cotización (RFQ) creadas por empleados desde el portal.

    No se dan ACL de purchase al portal: todo pasa por sudo() en el controlador,
    con doble candado — el grupo "Portal: solicitar compras" y estar ligado a un
    empleado activo.
    """

    def _ma_portal_employee(self):
        """Empleado activo detrás del usuario del portal (o recordset vacío)."""
        user = request.env.user
        if not user.has_group('maintegradora_custom.group_portal_purchase_request'):
            return request.env['hr.employee']
        return request.env['hr.employee'].sudo().search([
            '|',
            ('user_id', '=', user.id),
            ('work_contact_id', '=', user.partner_id.id),
        ], limit=1)

    def _ma_check_rfq_access(self):
        employee = self._ma_portal_employee()
        if not employee:
            raise AccessError(_("Solo el personal de MA puede crear solicitudes de compra."))
        return employee

    def _ma_rfq_domain(self):
        return [('create_uid', '=', request.env.user.id), ('ma_portal_request', '=', True)]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        values['ma_can_request_rfq'] = bool(self._ma_portal_employee())
        if 'ma_rfq_count' in counters:
            values['ma_rfq_count'] = request.env['purchase.order'].sudo().search_count(
                self._ma_rfq_domain()
            ) if values['ma_can_request_rfq'] else 0
        return values

    @route(['/my/rfqs', '/my/rfqs/page/<int:page>'], type='http', auth='user', website=True)
    def ma_portal_my_rfqs(self, page=1, **kw):
        self._ma_check_rfq_access()
        PurchaseOrder = request.env['purchase.order'].sudo()
        domain = self._ma_rfq_domain()
        count = PurchaseOrder.search_count(domain)
        pager = portal_pager(
            url='/my/rfqs', total=count, page=page, step=self._items_per_page,
        )
        orders = PurchaseOrder.search(
            domain, order='create_date desc', limit=self._items_per_page, offset=pager['offset'],
        )
        values = self._prepare_portal_layout_values()
        values.update({
            'orders': orders,
            'page_name': 'ma_rfq',
            'default_url': '/my/rfqs',
            'pager': pager,
        })
        return request.render('maintegradora_custom.portal_my_rfqs', values)

    @route(['/my/rfqs/new'], type='http', auth='user', website=True, methods=['GET'])
    def ma_portal_new_rfq(self, **kw):
        self._ma_check_rfq_access()
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'ma_rfq',
            'vendors': request.env['res.partner'].sudo().search(
                [('supplier_rank', '>', 0)], order='name', limit=500),
            'products': request.env['product.product'].sudo().search(
                [('purchase_ok', '=', True)], order='name', limit=1000),
            'error': kw.get('error'),
        })
        return request.render('maintegradora_custom.portal_rfq_form', values)

    @route(['/my/rfqs/new'], type='http', auth='user', website=True, methods=['POST'])
    def ma_portal_create_rfq(self, **post):
        employee = self._ma_check_rfq_access()
        Partner = request.env['res.partner'].sudo()
        Product = request.env['product.product'].sudo()

        vendor = Partner.browse(int(post.get('partner_id') or 0)).exists()
        if not vendor or vendor.supplier_rank <= 0:
            return request.redirect('/my/rfqs/new?error=vendor')

        lines = []
        for product_id, qty, description in zip(
            request.httprequest.form.getlist('product_id'),
            request.httprequest.form.getlist('product_qty'),
            request.httprequest.form.getlist('description'),
        ):
            product = Product.browse(int(product_id or 0)).exists()
            if not product or not product.purchase_ok:
                continue
            try:
                quantity = float(qty or 0)
            except ValueError:
                continue
            if quantity <= 0:
                continue
            line = {'product_id': product.id, 'product_qty': quantity}
            if description:
                line['name'] = description
            lines.append((0, 0, line))

        if not lines:
            return request.redirect('/my/rfqs/new?error=lines')

        order = request.env['purchase.order'].sudo().create({
            'partner_id': vendor.id,
            'company_id': request.env.user.company_id.id,
            'origin': _("Portal - %s", employee.name),
            'user_id': False,  # el solicitante es del portal, no un comprador
            'ma_portal_request': True,
            'order_line': lines,
        })
        order.message_post(body=_(
            "Solicitud creada desde el portal por %(employee)s.%(note)s",
            employee=employee.name,
            note=(_("<br/>Nota: %s", post['note']) if post.get('note') else ''),
        ))
        return request.redirect('/my/rfqs')
