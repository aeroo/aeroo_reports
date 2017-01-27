=============
Aeroo Reports
=============
Aeroo Reports for Odoo v8.0

Installation
------------
 - Install the python library aerolib available at https://github.com/aeroo/aeroolib.git
    - git clone https://github.com/aeroo/aeroolib.git
    - cd aerolib
    - python setup.py install

 - Install the python library Genshi
    - pip install Genshi

 - Install libreoffice
    - apt-get install libreoffice, libreoffice-writer, openjdk-7-jre


Usage
-----

Spreadsheets
------------
In a spreadsheet, you must insert hyperlinks in order to display data dynamically.

Go to: Insert -> Hyperlink, then in the field URL, write python://your-python-expression

Displaying each element of a list on a seperate row:

|   | A                                        | B                        |
|---|------------------------------------------|--------------------------|
| 1 | Description                              | Unit Price               |
| 2 | python://for each="line in o.order_line" |                          |
| 3 | python://line.name                       | python://line.price_unit |
| 4 | python:///for                            |                          |
