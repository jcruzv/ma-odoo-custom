"""Pasa la configuración de los campos ma_* a los campos nativos.

ma_generate_project / ma_project_template_id / ma_generate_task se eliminaron:
bienes y servicios usan service_tracking + project_template_id.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'product_template'
           AND column_name = 'ma_generate_project'
    """)
    if not cr.fetchone():
        return

    cr.execute("""
        SELECT id, ma_project_template_id, COALESCE(ma_generate_task, TRUE)
          FROM product_template
         WHERE ma_generate_project IS TRUE
    """)
    rows = cr.fetchall()
    if not rows:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    for product_id, template_id, generate_task in rows:
        product = env['product.template'].browse(product_id).exists()
        if not product:
            continue
        product.service_tracking = 'task_in_project' if generate_task else 'project_only'
        if template_id:
            product.project_template_id = template_id
