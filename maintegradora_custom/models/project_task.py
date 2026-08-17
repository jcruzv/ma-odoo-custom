from odoo import api, models, fields


class ProjectTask(models.Model):
    _inherit = 'project.task'

    employee_ids = fields.Many2many(
        'hr.employee',
        'project_task_employee_rel', 'task_id', 'employee_id',
        string='Empleados asignados',
    )

    @property
    def TASK_PORTAL_READABLE_FIELDS(self):
        return super().TASK_PORTAL_READABLE_FIELDS | {'employee_ids'}

    @property
    def TASK_PORTAL_WRITABLE_FIELDS(self):
        # el core no deja escribir user_ids desde el portal (y su dominio exige
        # usuarios internos); los colaboradores asignan por empleado
        return super().TASK_PORTAL_WRITABLE_FIELDS | {'employee_ids'}

    def _sync_employee_collaborators(self):
        """Comparte el proyecto de la tarea (modo Editar) con el partner de cada empleado asignado."""
        # los colaboradores del portal también asignan empleados y no tienen
        # permisos sobre project.collaborator ni sobre el proyecto
        self = self.sudo()
        Collaborator = self.env['project.collaborator']
        for task in self:
            project = task.project_id
            if not project:
                continue
            partners = task.employee_ids.mapped(
                lambda e: e.work_contact_id or e.user_partner_id
            )
            if not partners:
                continue
            if project.privacy_visibility != 'portal':
                project.privacy_visibility = 'portal'
            existing = project.collaborator_ids.mapped('partner_id')
            for partner in partners - existing:
                Collaborator.create({
                    'project_id': project.id,
                    'partner_id': partner.id,
                    'limited_access': False,  # Editar (acceso completo)
                })
            # Suscribir como seguidores: el portal (My Projects) filtra por follower
            project.message_subscribe(partner_ids=partners.ids)

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        tasks._sync_employee_collaborators()
        return tasks

    def write(self, vals):
        res = super().write(vals)
        if 'employee_ids' in vals:
            self._sync_employee_collaborators()
        return res
