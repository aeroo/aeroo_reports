===============
Aeroo CMIS Test
===============
A module for testing the module report_aeroo_cmis.
Because a running instance of Alfresco at localhost:8080 is required to run the tests,
the tests are implemented in a seperate module. This will prevent the CI server from
running those tests.

In order to run the tests locally, you have to setup a vanilla instance of Alfresco
running at localhost:8080 (the default Alfresco port). The admin password must be admin.

The test fixture will create the required folders and documents in your Alfresco's
main repository if they do not exist already.
