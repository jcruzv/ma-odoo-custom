from odoo import _
from odoo.addons.project.controllers.portal import ProjectCustomerPortal


class MaProjectPortal(ProjectCustomerPortal):

    def _prepare_searchbar_sortings(self):
        sortings = super()._prepare_searchbar_sortings()
        # task_count es calculado sin store: no sirve para ordenar
        sortings.update({
            'status': {'label': _('Estado'), 'order': 'last_update_status'},
        })
        return sortings
