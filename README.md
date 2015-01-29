# Aeroo report for Odoo v8

**Alpha version of Aeroo Reports for odoo v8 aka OpenERP v8**

## Installation

1. Find libreoffice/openoffice with python2 uni bindings. (e.g. http://gist.github.com/nagyv/c353b8b8f293a700e30a)
2. Install [aeroolib](https://github.com/aeroo/aeroolib)
3. Install pycups for direct printing support (`pip install pycups`)
4. Add these addons to your odoo config file
5. Install the addons

## Creating aeroo reports

There is a sample app in the repo that uses several aeroo features.

For simpler reports, the following xml fragment can give you the necessary setup, 
and your only task will be to create the report templates:

```xml
<report id="myreport"
  string="Report's name"
  model="res.partner"
  report_type="aeroo"
  file="my_addon/path/to/template/mytemplate.odt"
  name="dotted.name.for.the.report"
/>

  <record id="myreport" model="ir.actions.report.xml">
  <field name="in_format">oo-odt</field>
  <field name="tml_source">file</field>
</record>
```
