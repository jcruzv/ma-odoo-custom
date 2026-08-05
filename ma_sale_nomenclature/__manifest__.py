{
    'name': 'MA Sale Order Nomenclature',
    'version': '1.1',
    'category': 'Sales',
    'summary': 'Nomenclatura de órdenes de venta y generación de proyectos',
    'description': """
        Personaliza la estructura del nombre (folio) de las órdenes de venta.
        Estructura: PREFIJO-MES/AÑO-CLIENTE-FOLIO
        Ejemplo: O-EV-0626-123456-1234

        Además ajusta la generación de proyectos al confirmar la orden:
        - cada línea de servicio genera su propio proyecto, aunque varias líneas
          apunten a la misma plantilla;
        - todos los bienes de la orden comparten un único proyecto;
        - los bienes pueden usar "Crear en la orden" / "Plantilla de proyecto",
          que Odoo reserva a los servicios.
    """,
    'author': 'MA',
    'depends': ['sale_management', 'project', 'sale_project'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ma_category_type_data.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/project_project_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
