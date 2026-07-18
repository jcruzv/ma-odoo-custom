from odoo import api, models, fields


class ProjectProject(models.Model):
    _inherit = 'project.project'

    employee_ids = fields.Many2many(
        'hr.employee',
        'project_project_employee_rel', 'project_id', 'employee_id',
        string='Empleados asignados',
    )

    def _sync_employee_collaborators(self):
        """Comparte el proyecto (modo Editar) con el partner de cada empleado asignado."""
        Collaborator = self.env['project.collaborator']
        for project in self:
            partners = project.employee_ids.mapped(
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
        projects = super().create(vals_list)
        projects._sync_employee_collaborators()
        return projects

    def write(self, vals):
        res = super().write(vals)
        if 'employee_ids' in vals:
            self._sync_employee_collaborators()
        return res
