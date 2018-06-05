# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

from odoo.exceptions import except_orm

class ConnectionError(except_orm):
    """ Basic connection error.
    Example: When try to connect Aeroo DOCS and connection fails."""
    def __init__(self, msg):
        super(ConnectionError, self).__init__(msg)
        
        
class ProgrammingError(except_orm):
    """ Basic programming error.
    Example: When python code can not be compiled due to some error."""
    def __init__(self, msg):
        super(ProgrammingError, self).__init__(msg)
