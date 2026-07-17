from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    employee_ids = fields.Many2many(
        'hr.employee',
        'project_task_employee_rel', 'task_id', 'employee_id',
        string='Empleados asignados',
    )
