{
    'name': 'MA Sale Order Nomenclature',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Custom nomenclature for Sales Orders based on product categories',
    'description': """
        Este módulo personaliza la estructura del nombre (folio) de las órdenes de venta.
        Estructura: PREFIJO-MES/AÑO-CLIENTE-FOLIO
        Ejemplo: O-EV-0626-123456-1234
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
