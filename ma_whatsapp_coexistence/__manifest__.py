{
    'name': 'MA WhatsApp Coexistence',
    'version': '1.0',
    'category': 'Productivity/WhatsApp',
    'summary': 'Muestra en Odoo los mensajes enviados desde la app de WhatsApp Business',
    'description': """
        Soporte para los webhooks de WhatsApp Coexistence, que el módulo nativo
        ignora: smb_message_echoes (mensajes que el empleado envía desde la app
        del celular) y smb_app_state_sync.

        Los echoes se publican en el canal de Discuss correspondiente al número
        del cliente, sin reenviarlos por la API (que duplicaría el mensaje).
    """,
    'author': 'MA',
    'depends': ['whatsapp'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
