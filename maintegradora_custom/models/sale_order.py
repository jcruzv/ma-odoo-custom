import datetime
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sender_partner_id = fields.Many2one('res.partner', string='Correo emisor')
    availability_start = fields.Datetime(string='Disponibilidad desde')
    availability_end = fields.Datetime(string='Disponibilidad hasta')
    appointment_duration = fields.Float(string='Duración de la cita (horas)')
    appointment_status = fields.Selection([
        ('Pendiente', 'Pendiente'),
        ('Enviada', 'Enviada'),
        ('Agendada', 'Agendada'),
        ('Cancelada', 'Cancelada')
    ], string='Estatus de la cita', default='Pendiente')
    appointment_url = fields.Char(string='Liga para agendar cita')
    quote_link = fields.Char(string='Enlace de cotización')
    
    def _default_cover_text(self):
        return '''<div data-oe-version="2.0">Agradecemos su preferencia y a la vez enviamos esta cotización para su revisión.</div><div><br></div><div>A continuación, desglosamos todos los aspectos relacionados a la cotización.</div><div><br></div><div>Este documento abarca lo siguiente:</div><div><br></div><ul><li>Alcance</li><li>Tiempo de elaboración y gestión</li><li>Facilidades para el equipo de Integradora de Productos y Servicios Solano S.A. de C.V.</li><li>Condiciones comerciales/técnicas y vigencia, aceptación/cancelación o aplazamiento de la entrega del producto y servicio.</li><li>Código de Ética y Protección de datos personales.</li></ul><div><br></div><div>Esperamos servirles para todas sus necesidades, en la cual siempre estaremos comprometidos.</div><div><br></div><div>Saludos cordiales.</div>'''

    def _default_note(self):
        return '''<div data-oe-version="2.0"><strong>2. Alcance</strong></div><div><br></div><ul><li><strong>Señalamientos, extintores y aspectos de emergencia/ Alertamiento Sísmico:</strong> Se asignará al área de Operaciones para la correcta gestión de su servicio e instalación de este. Nuestro equipo ya cuenta con equipo optimo para la instalación de este, así como Equipo de Protección Personal correspondiente.</li><li><strong>Estructural: </strong>Se asignará a un Director Responsable de Obra para la emisión de sus dictámenes estructurales. En el informe se contempla anexar el carnet del arquitecto, así como su registro ante SEDUVI.</li><li><strong>Eléctrico: </strong>Se asignará a una Unidad Verificadora (UVIE) para la visita de las instalaciones, así como para la emisión del reporte correspondiente.</li></ul><div><strong><br></strong></div><div><strong>3. Tiempo de entrega y descripción del servicio</strong></div><div><br></div><ul><li><strong>Instalación de Señalamientos, extintores y aspectos de emergencia/ Alertamiento Sísmico: </strong>5 días hábiles. (Lunes a Viernes).</li><li><strong>Estructural: </strong>5 días hábiles (Lunes a Viernes)</li><li><strong>Eléctrico: </strong>20 días hábiles (Lunes a Viernes)</li></ul><div><strong>4. Facilidades para el equipo de MA Integradora</strong></div><div><br></div><div><span class="oe-tabs" style="width: 40px;">   </span>Le pedimos por favor nos permita ingresar nuestro vehículo corporativo, así como al personal</div><div><span class="oe-tabs" style="width: 40px;">      </span>designado para realizar correctamente el servicio.</div><div><br></div><div><strong>5. Condiciones comerciales/técnicas y vigencia de cotización.</strong></div><div><strong>a. Condiciones de pago</strong></div><ul><li>Se requiere el 50% del pago al aceptar la propuesta comercial y el 50% restante al finalizar el servicio.</li></ul><div><strong>b. Vigencia y aceptación/cancelación o aplazamiento del servicio</strong></div><div><br></div><ul><li>La presente cotización tiene una vigencia de 15 días naturales.</li><li>Esta propuesta será validada mediante una Orden de Compra (OC), la firma de un contrato o firma autógrafa de este documento.</li><li>La cancelación o aplazamiento de la entrega de la realización del servicio o producto se tendrá que realizar con 24 horas de anticipación, de lo contrario se multará al cliente con un 10% de esta propuesta económica. Este porcentaje no se contempla como pago parcial de servicio previamente autorizado.</li><li><strong>Integradora de Productos y Servicios Solano S.A. de C.V.</strong> no se hace responsable si el cliente envía información parcial, incompleta o incorrecta. Por lo que una vez realizado el pago ya sea parcial o total, no se realizará devoluciones si es que se llega a cancelar el servicio.</li></ul><div><br></div><div><strong>6. Código de Ética y Protección de datos personales</strong></div><div><br></div><div><span class="oe-tabs" style="width: 40px;">     </span>Con base en la Ley Federal de Protección de Datos Personales se le informa a todos los clientes y probables clientes que Integradora de Productos y Servicios Solano S.A. de C.V. recabará y tratará los datos personales que sean estrictamente necesarios para cumplir con los objetivos señalados en esta propuesta económica.</div><div><span class="oe-tabs" style="width: 40px;"> </span><br></div><div><span class="oe-tabs" style="width: 40px;">     </span>Para cualquier queja, comentario o sugerencia, puede enviar un correo con dicha información a la siguiente dirección <a href="mailto:contacto@maintegradora.com">contacto@maintegradora.com</a> donde se le dará seguimiento a la situación.</div><div><span class="oe-tabs" style="width: 40px;">       </span><br></div><div><span class="oe-tabs" style="width: 40px;">      </span>Las partes se comprometen a dar cabal cumplimento al Código de Ética que Integradora de Productos y Servicios Solano S.A. de C.V. tenga vigente y que puede ser consultado en nuestra página de internet <a href="http://www.maintegradora.com">www.maintegradora.com</a>.<br><br><br></div>'''

    note = fields.Html(default=_default_note)
    cover_text = fields.Html(string='Texto Portada', default=_default_cover_text)
    loaned_product_ids = fields.One2many('sale.loaned.product', 'sale_order_id', string='Productos Prestados')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for order in records:
            order._portal_ensure_token()
            order.quote_link = f"{base_url}{order.access_url}?access_token={order.access_token}"

        return records

    def _action_confirm(self):
        res = super()._action_confirm()
        self._ma_generate_projects_from_templates()
        return res

    def _ma_generate_projects_from_templates(self):
        """Permite que CUALQUIER producto (bien, servicio o combo) con
        project_template_id cree el proyecto desde la plantilla al confirmar.
        El nativo (sale_project) solo lo hace para servicios con service_tracking;
        aqui cubrimos los demas. 1 proyecto por orden, sin duplicar."""
        NATIVE_TRACKING = ('project_only', 'task_in_project', 'task_global_project')
        for order in self:
            if order.project_id:
                continue  # ya hay proyecto (nativo por servicio, o previo)
            for line in order.order_line:
                product = line.product_id.product_tmpl_id
                if not product.project_template_id or line.project_id:
                    continue
                # el nativo ya maneja servicios con rastreo -> no duplicar
                if line.is_service and product.service_tracking in NATIVE_TRACKING:
                    continue
                project = line._timesheet_create_project()
                order.project_id = project
                break

    def action_generate_appointment(self):
        self.ensure_one()
        if not self.availability_start or not self.availability_end:
            return

        DESFASE_HORARIO = -6
        fecha_inicio_utc = self.availability_start
        fecha_final_utc = self.availability_end
        fecha_inicio = fecha_inicio_utc + datetime.timedelta(hours=DESFASE_HORARIO)
        fecha_final = fecha_final_utc + datetime.timedelta(hours=DESFASE_HORARIO)

        duracion_cita = self.appointment_duration or 1.0
        slots = []
        delta = datetime.timedelta(days=1)
        fecha_actual = fecha_inicio.date()

        while fecha_actual <= fecha_final.date():
            if fecha_actual.weekday() < 5:
                if fecha_actual == fecha_inicio.date():
                    start_hour = fecha_inicio.hour + fecha_inicio.minute / 60.0
                else:
                    start_hour = 9.0

                if fecha_actual == fecha_final.date():
                    end_hour = fecha_final.hour + fecha_final.minute / 60.0
                else:
                    end_hour = 16.0

                if start_hour < end_hour:
                    slots.append((0, 0, {
                        'weekday': str(fecha_actual.weekday() + 1),
                        'start_hour': start_hour,
                        'end_hour': end_hour,
                    }))

            fecha_actual += delta

        appointment_id = self.env["appointment.type"].create({
            "name": f"Orden {self.name} | Cita con {self.partner_id.name}",
            "appointment_duration": duracion_cita,
            "slot_creation_interval": 1.0,
            "category_time_display": 'punctual_fields',
            "start_datetime": fecha_inicio_utc,
            "end_datetime": fecha_final_utc,
            'slot_ids': slots,
            "related_sale_order_id": self.id,
        })

        self.appointment_status = "Enviada"

        appointment_link = self.env['appointment.invite'].create({
            'appointment_type_ids': [appointment_id.id],
        })

        self.appointment_url = appointment_link.book_url

        template = self.env['mail.template'].browse(45)
        if template.exists():
            template.send_mail(self.id, force_send=True)

        appointment_id.write({'appointment_invite_ids': [(4, appointment_link.id)]})

