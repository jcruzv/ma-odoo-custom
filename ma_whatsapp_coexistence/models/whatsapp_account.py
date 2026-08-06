import logging
import mimetypes
import re

from markupsafe import Markup

from odoo import _, models
from odoo.addons.whatsapp.tools import phone_validation as wa_phone_validation
from odoo.addons.whatsapp.tools.whatsapp_api import WhatsAppApi
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)

MEDIA_TYPES = ('document', 'image', 'audio', 'video', 'sticker')


class WhatsappAccount(models.Model):
    _inherit = 'whatsapp.account'

    def _process_smb_message_echoes(self, value):
        """Publica en Discuss los mensajes que el negocio envía desde la app del celular.

        Coexistence manda un echo por cada mensaje que sale de la app. Se registran
        con 'whatsapp_inbound_msg_uid' para que el canal NO los reenvíe por la API
        (eso duplicaría el mensaje al cliente), y después se corrigen a outbound.
        """
        self.ensure_one()
        wa_api = WhatsAppApi(self)

        for echo in value.get('message_echoes', []):
            msg_uid = echo.get('id')
            if not msg_uid:
                continue
            if self.env['whatsapp.message'].sudo().search_count([('msg_uid', '=', msg_uid)]):
                continue  # echo repetido: Meta reintenta hasta recibir 200

            recipient = self._wa_format_number(echo.get('to', ''))
            if not recipient:
                _logger.warning("Echo sin destinatario: %s", echo)
                continue

            kwargs = self._prepare_echo_message(echo, wa_api)
            if kwargs is None:
                continue

            channel = self._find_active_channel(recipient, create_if_not_found=True)
            kwargs.update({
                'message_type': 'whatsapp_message',
                'author_id': self.env.company.partner_id.id,
                'subtype_xmlid': 'mail.mt_comment',
                'whatsapp_inbound_msg_uid': msg_uid,
            })
            message = channel.message_post(**kwargs)
            # El canal lo dio de alta como entrante; en realidad salió del negocio.
            message.wa_message_ids.sudo().write({'message_type': 'outbound', 'state': 'sent'})

    def _prepare_echo_message(self, echo, wa_api):
        """Devuelve los kwargs de message_post para un echo, o None si se ignora."""
        echo_type = echo.get('type')

        if echo_type == 'text':
            return {'body': plaintext2html(echo['text']['body'])}

        if echo_type in MEDIA_TYPES:
            media = echo[echo_type]
            filename = media.get('filename')
            mime_type = media.get('mime_type')
            datas = wa_api._get_whatsapp_document(media['id'])
            if not filename:
                filename = echo_type + (mimetypes.guess_extension(mime_type or '') or '')
            kwargs = {'attachments': [(filename, datas, {'voice': media.get('voice')})]}
            if media.get('caption'):
                kwargs['body'] = plaintext2html(media['caption'])
            return kwargs

        if echo_type == 'location':
            loc = echo['location']
            url = Markup("https://maps.google.com/maps?q={lat},{lng}").format(
                lat=loc['latitude'], lng=loc['longitude'])
            body = Markup('<a target="_blank" href="{url}"><i class="fa fa-map-marker"/> {label}</a>').format(
                url=url, label=_("Location"))
            if loc.get('name'):
                body += Markup("<br/>{name}").format(name=loc['name'])
            return {'body': body}

        if echo_type == 'contacts':
            body = Markup()
            for contact in echo.get('contacts', []):
                body += Markup("<i class='fa fa-address-book'/> {name}<br/>").format(
                    name=contact.get('name', {}).get('formatted_name', ''))
                for phone in contact.get('phones', []):
                    body += Markup("{type}: {number}<br/>").format(
                        type=phone.get('type'), number=phone.get('phone'))
            return {'body': body}

        if echo_type == 'edit':
            edited = echo.get('edit', {}).get('message', {})
            inner_type = edited.get('type')
            text = edited.get(inner_type, {}).get('body') or edited.get(inner_type, {}).get('caption') or ''
            return {'body': Markup("<i>{label}</i> {text}").format(
                label=_("(mensaje editado desde la app)"), text=text)}

        if echo_type == 'revoke':
            return {'body': Markup("<i>{label}</i>").format(
                label=_("(mensaje eliminado desde la app)"))}

        _logger.warning("Tipo de echo no soportado: %s", echo)
        return None

    def _wa_format_number(self, number):
        """Normaliza el número del echo al formato que usa el módulo (sin '+')."""
        if not number:
            return False
        cleaned = "+" + re.sub(r"\D", "", number)
        return wa_phone_validation.wa_phone_format(
            self,
            country=None,
            number=cleaned,
            force_format="WHATSAPP",
            raise_exception=False,
        ) or cleaned
