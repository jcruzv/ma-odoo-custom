from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = 'project.project'

    employee_ids = fields.Many2many(
        'hr.employee',
        'project_project_employee_rel', 'project_id', 'employee_id',
        string='Empleados asignados',
    )
