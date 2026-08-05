from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ma_category_area = fields.Selection([
        ('operaciones', 'OPERACIONES'),
        ('girpc', 'GIRPC'),
        ('stps', 'STPS'),
        ('ambiental', 'AMBIENTAL'),
        ('ui', 'UI')
    ], string='Área MA')
    
    ma_category_type_ids = fields.Many2many(
        'ma.category.type',
        string='Tipos de Servicio MA'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = vals.get('name', _('New'))
            if not name or name in (_('New'), 'New', 'Nuevo', '/'):
                area = vals.get('ma_category_area')
                type_ids_commands = vals.get('ma_category_type_ids', [])
                
                # Command format is usually [(6, 0, [ids])]
                type_ids = []
                for command in type_ids_commands:
                    if len(command) == 3 and command[0] == 6:
                        type_ids = command[2]
                        break
                    elif len(command) == 3 and command[0] == 4:
                        type_ids.append(command[1])
                        
                if area and type_ids:
                    types = self.env['ma.category.type'].browse(type_ids)
                    if area == 'ui' and any(t.code == 'D' for t in types):
                        vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or 'New'
                    else:
                        area_code_map = {
                            'operaciones': 'O',
                            'girpc': 'G',
                            'stps': 'S',
                            'ambiental': 'A',
                            'ui': 'U'
                        }
                        area_code = area_code_map.get(area, 'X')
                        type_codes = '-'.join(sorted(set(t.code for t in types)))
                        prefix = f"{area_code}-{type_codes}"
                        
                        mmyy = fields.Datetime.now().strftime('%m%y')
                        partner_id = vals.get('partner_id')
                        client_ref = str(partner_id).zfill(6) if partner_id else '000000'
                        folio = self.env['ir.sequence'].next_by_code('ma.sale.order.custom') or '0001'
                        
                        vals['name'] = f"{prefix}-{mmyy}-{client_ref}-{folio}"
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or 'New'
                        
        return super(SaleOrder, self).create(vals_list)

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        
        # Solo actualizar si se modifican las categorías o el cliente, y si no estamos ya actualizando el nombre
        if ('ma_category_area' in vals or 'ma_category_type_ids' in vals or 'partner_id' in vals) and 'name' not in vals:
            for order in self:
                # Evitar cambiar el nombre de órdenes que ya están confirmadas o canceladas
                if order.state not in ['draft', 'sent']:
                    continue
                    
                area = vals.get('ma_category_area', order.ma_category_area)
                
                if area and order.ma_category_type_ids:
                    if area == 'ui' and any(t.code == 'D' for t in order.ma_category_type_ids):
                        pass # Mantenemos el que tiene
                    else:
                        area_code_map = {
                            'operaciones': 'O',
                            'girpc': 'G',
                            'stps': 'S',
                            'ambiental': 'A',
                            'ui': 'U'
                        }
                        area_code = area_code_map.get(area, 'X')
                        type_codes = '-'.join(sorted(set(t.code for t in order.ma_category_type_ids)))
                        new_prefix = f"{area_code}-{type_codes}"
                        
                        current_name = order.name
                        folio = '0001'
                            
                        # Intentar extraer el folio del nombre actual (asumiendo que es el último bloque de dígitos)
                        parts = current_name.split('-')
                        if len(parts) >= 4 and parts[-1].isdigit():
                            folio = parts[-1]
                        else:
                            # Si era un nombre estándar como S00004, extraemos sus números
                            digits = ''.join([c for c in current_name if c.isdigit()])
                            if digits:
                                folio = digits
                            else:
                                folio = self.env['ir.sequence'].next_by_code('ma.sale.order.custom') or '0001'
                        
                        date_order = order.date_order or fields.Datetime.now()
                        mmyy = date_order.strftime('%m%y')
                        
                        partner_id = order.partner_id
                        client_ref = str(partner_id.id).zfill(6) if partner_id else '000000'
                        
                        new_name = f"{new_prefix}-{mmyy}-{client_ref}-{folio}"
                        
                        if order.name != new_name:
                            order.write({'name': new_name})
                                
        return res

    def _action_confirm(self):
        """El core solo genera proyecto para líneas de servicio; aquí se cubren
        los bienes marcados con ma_generate_project."""
        res = super()._action_confirm()
        if not self.env.context.get('disable_project_task_generation'):
            for order in self:
                order.order_line.sudo().with_company(order.company_id)._ma_generate_projects()
        return res

    def _get_ma_custom_prefix(self, area, service_type):
        mapping = {
            'operaciones': {
                'extintores_v': 'O-EV',
                'extintores_r': 'O-ER',
                'extintores_m': 'O-EM',
                'instalaciones': 'O-I'
            },
            'girpc': {
                'pipc': 'G-P',
                'capacitacion': 'G-C',
                'gestiones': 'G-G'
            },
            'stps': {
                'implementacion': 'S-I',
                'capacitacion': 'S-C',
                'estudios': 'S-E'
            },
            'ambiental': {
                'gestiones': 'A-G',
                'capacitacion': 'A-C'
            }
        }
        return mapping.get(area, {}).get(service_type, '')
