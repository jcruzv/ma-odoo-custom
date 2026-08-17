from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def ma_employee(self):
        """Empleado activo detrás de este usuario (recordset, puede estar vacío)."""
        self.ensure_one()
        return self.env['hr.employee'].sudo().search([
            '|',
            ('user_id', '=', self.id),
            ('work_contact_id', '=', self.partner_id.id),
        ], limit=1)

    def ma_can_request_rfq(self):
        """Doble candado de las solicitudes de compra del portal: grupo + empleado."""
        self.ensure_one()
        if not self.has_group('maintegradora_custom.group_portal_purchase_request'):
            return False
        return bool(self.ma_employee())
