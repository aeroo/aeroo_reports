//##############################################################################
//
// This file is part of Aeroo Reports software - for license refer LICENSE file  
//
//##############################################################################

odoo.define('report_aeroo.report', function(require){
'use strict';

var ActionManager= require('web.ActionManager');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');

ActionManager.include({
    ir_actions_report: function (action, options){
        var self = this;
        var c_action = _.clone(action);
        if (c_action.report_type !== 'aeroo') {
            return self._super(action, options);
        }

        framework.blockUI();
        var aeroo_url = 'report/aeroo/' + c_action.report_name;
        if (_.isUndefined(action.data) || _.isNull(action.data) || (_.isObject(action.data) && _.isEmpty(action.data))) {
            if (action.context.active_ids) {
                aeroo_url += '/' + c_action.context.active_ids.join(',');
                // odoo does not send context if no data, but I find it quite useful to send it regardless data or no data
                aeroo_url += '?context=' + encodeURIComponent(JSON.stringify(c_action.context));
            }
        }else{
            aeroo_url += '/' + c_action.context.active_ids.join(',');
            aeroo_url += '?options=' + encodeURIComponent(JSON.stringify(c_action.data));
            aeroo_url += '&context=' + encodeURIComponent(JSON.stringify(c_action.context));
        }
        self.getSession().get_file({
            url: aeroo_url,
            data: {data: JSON.stringify([
                aeroo_url,
                c_action.report_type
            ])},
            error: crash_manager.rpc_error.bind(crash_manager),
            success: function (){
                if(c_action && options && !c_action.dialog){
                    options.on_close();
                }
            }
        });
        framework.unblockUI();
        return;
    }
});
});
