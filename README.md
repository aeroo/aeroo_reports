=============
Aeroo Reports
=============
Aeroo Reports for Odoo v8.0

# Installation

 - Install the python library aerolib available at https://github.com/aeroo/aeroolib.git
    - git clone https://github.com/aeroo/aeroolib.git
    - cd aerolib
    - python setup.py install

 - Install the python library Genshi
    - pip install Genshi

 - Install libreoffice
    - apt-get install libreoffice, libreoffice-writer, openjdk-7-jre


# Translations

The main difference between this fork of Aeroo reports and other similar reporting
engines for Odoo is the way it handles translations.

Most engines implement the standard way of Odoo to translate a document.
This implies that the template is writen in english and that all terms in the template
are stored in the database (as model ir.translation).
Every time you change a word in the template, you must update the translations and
test that it is translated correctly. Therefore, it is very inconvenient for someone
non-technical to maintain the report.

The philosophy in this fork of Aeroo is that the person who uses the report
(i.e. the accountant, the office manager, etc.) is the one who maintains the report,
not the developper.

## Different template per language

For each language that the report must support, you may create a template and bind it to the language.

* Go to: Settings -> Technical -> Reports -> Aeroo Reports
* Select your report
* In the field 'Template Source', select 'Different Template per Language'
* In the field 'Templates by Language', add a line that maps your language to a template.

If a template is not available for a language and a user tries to print the report in that language,
the system will raise an exception saying that the report is unavailable for the given language.

The language used for printing the template must be parametrized in the field 'Language Evaluation'
(by default: o.partner_id.lang).


# Importing a Template from a DMS

This feature has been tested with Alfresco, but it should work with any DMS compliant with the
CMIS protocol. The idea is to store and maintain the template(s) of a report in the DMS and
upload it into Odoo when generating the report.

If the DMS can not be reached when the user clicks for generating the report, the last
available version of the template is used. A message is logged in the dicsussion thread of the object
to track what report/version was generated.

## Configure the DMS connector

* Go to: Connectors -> Aeroo Reports / DMS
* Create a new backend
* Select the url / username / password that will be used to connect to the DMS
* Click on 'Update Repository List'

## Configure the report

* Go to: Settings -> Technical -> Reports -> Aeroo Reports
* Select your report
* In the field 'Template Source', select 'Import from DMS'
* In the field 'DMS Repository', select the DMS/repository to use.
* In the field 'DMS Path', enter the absolute path to template inside the DMS.

Note: in Alfresco Share, it is not an easy task to find the absolute path to a document.
I suggest to find it by trial and error until you figure a patern that works.

## Different template per language + Import from DMS

You may also import distinct templates per language from the DMS:

* In the field 'Template Source', select 'Different Template per Language'
* In the field 'DMS Repository', select the DMS/repository to use.
* In the field 'Templates by Language', add a line that maps your language to a template.
    - In the field 'Template Source', select 'Import From DMS'
    - In the field 'File Location', enter the absolute path to the template inside the DMS.


# Creating a Template

## Spreadsheets

In a spreadsheet, you must insert hyperlinks in order to display data dynamically.

Go to: Insert -> Hyperlink, then in the field URL, write python://your-python-expression

Displaying each element of a list on a seperate row:

|   | A                                        | B                        |
|---|------------------------------------------|--------------------------|
| 1 | Description                              | Unit Price               |
| 2 | python://for each="line in o.order_line" |                          |
| 3 | python://line.name                       | python://line.price_unit |
| 4 | python:///for                            |                          |
