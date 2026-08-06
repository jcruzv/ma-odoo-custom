import json
import logging

from werkzeug.exceptions import Forbidden

from odoo.addons.whatsapp.controller.main import Webhook
from odoo.http import request

_logger = logging.getLogger(__name__)

COEXISTENCE_FIELDS = ('smb_message_echoes', 'smb_app_state_sync')


class WebhookCoexistence(Webhook):

    def webhookpost(self):
        """Atiende los webhooks de coexistence antes de delegar en el nativo.

        El controlador nativo solo mira el campo 'messages', así que los echoes
        (mensajes enviados desde la app del celular) se descartan en silencio.
        """
        data = json.loads(request.httprequest.data)
        for entry in data.get('entry', []):
            account = request.env['whatsapp.account'].sudo().search(
                [('account_uid', '=', entry['id'])], limit=1)
            if not account:
                continue
            for changes in entry.get('changes', []):
                if changes.get('field') not in COEXISTENCE_FIELDS:
                    continue
                # La firma se valida aquí porque el nativo no llega a estos campos.
                if not self._check_signature(account):
                    raise Forbidden()
                value = changes['value']
                phone_uid = value.get('metadata', {}).get('phone_number_id')
                wa_account = request.env['whatsapp.account'].sudo().search([
                    ('phone_uid', '=', phone_uid), ('account_uid', '=', entry['id'])], limit=1)
                if not wa_account:
                    _logger.warning("Coexistence webhook sin cuenta configurada: %s", value)
                    continue
                if changes['field'] == 'smb_message_echoes':
                    wa_account._process_smb_message_echoes(value)
                else:
                    _logger.info("smb_app_state_sync recibido: %s", value)

        return super().webhookpost()
