from odoo import models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        
        for picking in self:
            campo_loc = picking.location_id
            if not campo_loc:
                continue

            root = (campo_loc.complete_name or campo_loc.name or '').split('/')[0]

            scrap_loc = self.env['stock.location'].search([
                ('usage', '=', 'inventory'),
                ('complete_name', '=', root + '/Desecho'),
            ], limit=1)

            if not scrap_loc:
                continue

            for ml in picking.move_line_ids:
                demandado = ml.move_id.product_uom_qty or 0.0
                regresa = ml.qty_done or 0.0

                desechado = demandado - regresa
                if desechado <= 0:
                    continue

                scrap = self.env['stock.scrap'].create({
                    'product_id': ml.product_id.id,
                    'product_uom_id': ml.product_uom_id.id or ml.product_id.uom_id.id,
                    'scrap_qty': desechado,
                    'location_id': campo_loc.id,
                    'scrap_location_id': scrap_loc.id,
                    'picking_id': picking.id,
                    'origin': picking.name,
                    'lot_id': ml.lot_id.id if ml.lot_id else False,
                    'package_id': ml.package_id.id if ml.package_id else False,
                    'owner_id': ml.owner_id.id if ml.owner_id else False,
                })
                scrap.action_validate()
                
        return res
