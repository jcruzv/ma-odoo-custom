{
    'name': 'Maintegradora Custom',
    'version': '1.0',
    'category': 'Customizations',
    'summary': 'Custom logic and fields replacing Odoo Studio',
    'author': 'Antigravity',
    'depends': ['sale_management', 'stock', 'mail', 'appointment', 'project', 'hr', 'sale_project'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/product_template_views.xml',
        'views/project_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
