from odoo import models

class MailMail(models.Model):
    _inherit = 'mail.mail'

    def send(self, auto_commit=False, raise_exception=False):
        for mail in self:
            if mail.model == 'sale.order' and mail.res_id:
                order = self.env['sale.order'].browse(mail.res_id)
                if order.sender_partner_id:
                    partner = order.sender_partner_id
                    servidor = self.env['ir.mail_server'].search([('smtp_user', '=', partner.email)], limit=1)
                    if servidor:
                        mail.write({'mail_server_id': servidor.id, 'email_from': partner.email})
                    if mail.mail_message_id:
                        mail.mail_message_id.write({'author_id': partner.id})
        return super().send(auto_commit=auto_commit, raise_exception=raise_exception)
