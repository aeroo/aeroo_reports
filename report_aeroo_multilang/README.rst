.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

=====================================
Multilingual support for Aeroo Report
=====================================

This module extends the Aeroo Report functionality by letting you specify a rule to choose the appropriate
template to use according to an expected language.

Usage
=====

This module add two new fields on the report definition:

* Alternate report file path: This should be a placeholder expression that provides the path to an alternate report file to use
  for a given language. The the expression can use the string '{lang}' as placeholder in the path, 
  e.g. "folder/my_template_{lang}.odt". If the expression is not provided or can be resolved, the report falls back
  on the main report file path/controller.
* Language:  This should usually be a placeholder expression that provides the appropriate language,
  e.g. "${object.partner_id.lang}.". The 'object' in the expression is on instance of the model on which the
  report applies. 

Credits
=======

Contributors
------------

* Laurent Mignon <laurent.mignon@acsone.eu>

Maintainer
----------

.. image:: https://www.acsone.eu/logo.png
   :alt: ACSONE SA/NV
   :target: http://www.acsone.eu

This module is maintained by ACSONE SA/NV.
