
openerp.report_aeroo_printscreen = function (session) {
    var _t = session.web._t
    /**
     * ------------------------------------------------------------
     * Print Screen
     * ------------------------------------------------------------
     * 
     * Add a Print Screen option to the "Sidebar"
     */

    function print_screen(self, view) {
        var ids = view.get_selected_ids();
        var action = {
            type: 'ir.actions.report.xml',
            report_name: 'aeroo.printscreen.list',
            datas: {model:view.dataset.model, id:ids[0], report_type:'aeroo', ids:ids},
            context: {active_ids:ids, model:view.dataset.model, ids:ids}
        };
        session.client.action_manager.do_action(action);
    }

    /* Extend the Sidebar to add Print Screen link in the 'Print' menu */
    session.web.Sidebar = session.web.Sidebar.extend({

        start: function() {
            var self = this;
            this._super(this);
            self.add_items('print', [
                {   label: _t('Print Screen'),
                    callback: self.on_click_print_screen,
                    action: self.on_click_print_screen,
                    classname: 'oe_sidebar_print' },
            ]);
        },

        on_click_print_screen: function(item) {
            var view = this.getParent()
            print_screen(this, view);
        },

    });
};
