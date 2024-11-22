# data migration tool

This tool is designed to efficiently transfer data from one Salesforce org to another. The tool aims to streamline the migration process by ensuring accurate data mapping, maintaining record relationships, and adhering to Salesforce's API and governor limits. It facilitates data migration across standard and custom objects, while preserving data integrity, security, and field-level permissions. The migration tool is designed to handle large data volumes through optimized batching and bulk API usage, with built-in error logging, retry mechanisms, and post-migration validation to ensure data consistency. By addressing key challenges like heap size limitations, API call limits, and data dependencies, the tool provides a robust solution for seamless Salesforce org-to-org data transfers.


Key Considerations:

1. Data Mapping:

    * Ensure that the fields from the source org are correctly mapped to the fields in the target org, including handling custom fields, standard objects, and custom objects.

1. Order of Migration:

    * Migrate data in a logical order to respect dependencies (e.g., Accounts before Contacts, Parent before Child relationships).
    * Address record relationships using Salesforce IDs, External IDs, or mapping strategies.

1. Bulk API vs. REST API:

    * Salesforce provides various APIs (Bulk API, REST API, SOAP API). The Bulk API is optimized for large data volumes but has limitations like delayed processing, while the REST API offers more flexibility for smaller transactions.

1. Data Integrity:

    * Maintain data quality and integrity during migration, ensuring data relationships and formats remain consistent.
    * Use validation rules and error handling mechanisms to prevent data corruption.

1. Handling Salesforce Limits:

    * Salesforce has limits like API call limits, heap size, governor limits, and batch sizes. Optimize to handle these constraints efficiently.

1. Field-Level Security & Sharing Settings:

    * Ensure that field-level security, sharing settings, and permissions are respected when migrating data to avoid unauthorized data exposure.

1. Error Logging & Retry Mechanism:

    * Implement detailed logging and error handling to track failed records and allow for easy retries.

1. Post-Migration Data Validation:

    * After the migration, run validation processes to ensure data consistency between the source and target orgs.



Solution

The solution involves building a Python-based tool to facilitate the migration of data between two Salesforce orgs. This tool leverages Salesforce's REST and Bulk APIs to handle large volumes of data efficiently while respecting API limits and maintaining data integrity across standard and custom objects. Key aspects of the solution include:


Tool Details

Data Migration Tool

```

./data_migration_tool
└── sfdc
    ├── configurations // captures the configurations
    │   ├── migration_configurations // #local orgs only
    │   ├── object_configurations // has object and field mappings to be configured
    │   ├── object_configurations_workset // describer generated object and field mappings
    │   ├── object_matchingkey_configurations // global unique identifiers for every object
    │   ├── org_configurations // source and destination org credentials for migrations
    │   ├── org_configurations_local // #local orgs only
    │   └── org_configurations_template // source and destination org credentials template
    ├── dtos // #python data transfer objects
    │   └── configurations_dtos
    │       └── __pycache__
    ├── results // #export results
    │   └── 2f54c928c256447dab3397cfee806948 // #export results folders
    │       ├── $namespace$__objectclass__c
    │       ├── $namespace$__pricelist__c
    │       ├── $namespace$__pricelistentry__c
    │       ├── $namespace$__pricingelement__c
    │       ├── $namespace$__productchilditem__c
    │       ├── $namespace$__promotion__c
    │       ├── $namespace$__promotionitem__c
    │       ├── $namespace$__timeplan__c
    │       ├── $namespace$__timepolicy__c
    │       ├── pricebook2
    │       ├── pricebookentry
    │       ├── product2
    │       └── recordtype
    └── services // #python services for migration
```


* One Time Environment Setup
    * Script setup and installation
        * Install Python 3 for your environment from https://www.python.org/ for your machine
        * Create and activate a virtual environment:
            * Windows:
                ```bash
                python -m venv .env
                .env\Scripts\activate
                ```
            * macOS/Linux:
                ```bash
                python3 -m venv .env
                source .env/bin/activate
                ```

        * Install dependencies:
            ```bash
            pip install -r requirements.txt
    * Setup Org Credentials
        * go to below location in the project to see source and destination org configuration files
            * data_migration_tool > sfdc > configurations > org_configurations_template
            * 
        * copy those files to 
            * data_migration_tool > sfdc > configurations > org_configurations
        * now update each of the files with relevant org information as shown below
            * {
                  "username": "<username>",
                  "password": "<password>",
                  "consumer_key": "<consumer_key>",
                  "consumer_secret": "<consumer_secret>",
                  "domain": "test/production",
                  "instance_url" : "https://test.salesforce.com",
                  "namespace": "namespace"
                }
    * SObject Metadata Scraping
        * For migration tool to work, we need run describer tool in the script to list out all the possible objects that could be migrated from your org 
            * go to below location in the project to see all the objects names that this tool supports for migration
                * data_migration_tool > sfdc > configurations > object_matchingkey_configurations > matchingkeys.json
            * by default, have added a list of objects required for CME with reference from VBT(Vlocity Build Tool), please update the list for any new objects or matching keys
            * ```{
                    "$namespace$__attribute__c" : "$namespace$__code__c",
                    "$namespace$__attributeassignment__c" : "$namespace$__objectid__c,$namespace$__attributeid__c,$namespace$__isoverride__c",
                    "$namespace$__attributeassignmentrule__c" : "name",
                    "$namespace$__attributecategory__c" : "$namespace$__code__c",
                    "$namespace$__calculationmatrix__c" : "name",
                    "$namespace$__calculationmatrixversion__c" : "$namespace$__versionnumber__c,$namespace$__calculationmatrixid__c",
                    "$namespace$__calculationprocedure__c" : "name",
                    "$namespace$__calculationprocedureversion__c" : "$namespace$__versionnumber__c,$namespace$__calculationprocedureid__c",
                    "$namespace$__catalog__c" : "$namespace$__globalkey__c",
                    "$namespace$__catalogproductrelationship__c" : "$namespace$__catalogid__c,$namespace$__product2id__c",
                    "$namespace$__catalogrelationship__c" : "$namespace$__childcatalogid__c,$namespace$__parentcatalogid__c",
                    "$namespace$__contextaction__c" : "$namespace$__globalkey__c",
                    "$namespace$__contextdimension__c" : "$namespace$__globalkey__c",
                    "$namespace$__contextscope__c" : "$namespace$__globalkey__c",
                    "$namespace$__contracttype__c" : "name",
                    "$namespace$__contracttypesetting__c" : "name,$namespace$__contracttypeid__c",
                    "$namespace$__documentclause__c" : "name",
                    "$namespace$__documenttemplate__c" : "$namespace$__externalid__c",
                    "$namespace$__drbundle__c" : "name",
                    "$namespace$__drmapitem__c" : "$namespace$__mapid__c",
                    "$namespace$__element__c" : "$namespace$__omniscriptid__c,name",
                    "$namespace$__entityfilter__c" : "$namespace$__globalkey__c",
                    "$namespace$__interfaceimplementation__c" : "name",
                    "$namespace$__interfaceimplementationdetail__c" : "$namespace$__interfaceid__c,name",
                    "$namespace$__objectclass__c" : "$namespace$__globalkey__c",
                    "$namespace$__objectruleassignment__c" : "$namespace$__globalkey__c",
                    "$namespace$__objectlayout__c" : "$namespace$__globalkey__c",
                    "$namespace$__offeringprocedure__c" : "name",
                    "$namespace$__picklist__c" : "$namespace$__globalkey__c",
                    "$namespace$__picklistvalue__c" : "$namespace$__globalkey__c",
                    "$namespace$__pricelist__c" : "$namespace$__code__c",
                    "$namespace$__pricelistentry__c" : "$namespace$__globalkey__c",
                    "$namespace$__pricingelement__c" : "$namespace$__globalkey__c",
                    "$namespace$__pricingvariable__c" : "$namespace$__code__c",
                    "$namespace$__productchilditem__c" : "$namespace$__globalkey__c",
                    "$namespace$__productconfigurationprocedure__c" : "$namespace$__globalkey__c",
                    "$namespace$__productrelationship__c" : "$namespace$__globalkey__c",
                    "$namespace$__promotion__c" : "$namespace$__globalkey__c",
                    "$namespace$__promotionitem__c" : "nos_t_matchingkey__c",
                    "$namespace$__publicprogram__c" : "name",
                    "$namespace$__querybuilder__c" : "name",
                    "$namespace$__rule__c" : "$namespace$__globalkey__c",
                    "$namespace$__storyobjectconfiguration__c" : "name",
                    "$namespace$__timeplan__c" : "$namespace$__globalkey__c",
                    "$namespace$__timepolicy__c" : "$namespace$__globalkey__c",
                    "$namespace$__uifacet__c" : "$namespace$__globalkey__c",
                    "$namespace$__uisection__c" : "$namespace$__globalkey__c",
                    "$namespace$__vlocityaction__c" : "name",
                    "$namespace$__vlocityattachment__c" : "$namespace$__globalkey__c",
                    "$namespace$__vlocitycard__c" : "name,$namespace$__author__c,$namespace$__version__c",
                    "$namespace$__vlocityfunction__c" : "$namespace$__globalkey__c",
                    "$namespace$__vlocityfunctionargument__c" : "$namespace$__globalkey__c",
                    "$namespace$__vlocitysearchwidgetactionssetup__c" : "$namespace$__vlocityactionid__c,$namespace$__vlocitysearchwidgetsetupid__c,$namespace$__actiontype__c",
                    "$namespace$__vlocitysearchwidgetsetup__c" : "name",
                    "$namespace$__vlocitystate__c" : "name,$namespace$__dtpstatemodelname__c",
                    "$namespace$__vlocitystatemodel__c" : "$namespace$__objectapiname__c,$namespace$__fieldapiname__c,$namespace$__typefieldname__c,$namespace$__typefieldvalue__c",
                    "$namespace$__vlocitystatemodelversion__c" : "$namespace$__versionnumber__c,$namespace$__statemodelid__c",
                    "$namespace$__vlocityuilayout__c" : "name,$namespace$__version__c,$namespace$__author__c",
                    "$namespace$__vlocityuitemplate__c" : "name,$namespace$__author__c,$namespace$__version__c",
                    "$namespace$__vqmachine__c" : "name",
                    "$namespace$__vqmachineresource__c" : "$namespace$__vqmachineid__c,$namespace$__vqresourceid__c",
                    "$namespace$__vqresource__c" : "name",
                    "document" : "developername",
                    "pricebook2" : "name",
                    "pricebookentry" : "product2id,pricebook2id,currencyisocode",
                    "product2" : "$namespace$__globalkey__c",
                    "recordtype" : "developername,sobjecttype",
                    "user" : "email"
                }
   
    * Object Mapping and Transformation:
        * Based on the list of objects available in matchingkeys.json, we have build a service called describer to load all the metadata related to an sobject along with its references and possible child references
        * in terminal , go to 
            * data_migration_tool > sfdc
        * execute following command
            * python3 describer.py
        * Which would fetch metadata related to all the sobject mappings in your workset directory as shown below
            * data_migration_tool > sfdc > configurations > object_configurations_workset
            * ```./object_configurations_workset
                ├── $namespace$__attribute__c.json
                ├── $namespace$__attributeassignment__c.json
                ├── $namespace$__attributeassignmentrule__c.json
                ├── $namespace$__attributecategory__c.json
                ├── $namespace$__calculationmatrix__c.json
                ├── $namespace$__calculationmatrixversion__c.json
                ├── $namespace$__calculationprocedure__c.json
                ├── $namespace$__calculationprocedureversion__c.json
                ├── $namespace$__catalog__c.json
                ├── $namespace$__catalogproductrelationship__c.json
                ├── $namespace$__catalogrelationship__c.json
                ├── $namespace$__contextaction__c.json
                ├── $namespace$__contextdimension__c.json
                ├── $namespace$__contextscope__c.json
                ├── $namespace$__contracttype__c.json
                ├── $namespace$__contracttypesetting__c.json
                ├── $namespace$__documentclause__c.json
                ├── $namespace$__documenttemplate__c.json
                ├── $namespace$__drbundle__c.json
                ├── $namespace$__drmapitem__c.json
                ├── $namespace$__element__c.json
                ├── $namespace$__entityfilter__c.json
                ├── $namespace$__interfaceimplementation__c.json
                ├── $namespace$__interfaceimplementationdetail__c.json
                ├── $namespace$__objectclass__c.json
                ├── $namespace$__objectlayout__c.json
                ├── $namespace$__objectruleassignment__c.json
                ├── $namespace$__offeringprocedure__c.json
                ├── $namespace$__picklist__c.json
                ├── $namespace$__picklistvalue__c.json
                ├── $namespace$__pricelist__c.json
                ├── $namespace$__pricelistentry__c.json
                ├── $namespace$__pricingelement__c.json
                ├── $namespace$__pricingvariable__c.json
                ├── $namespace$__productchilditem__c.json
                ├── $namespace$__productconfigurationprocedure__c.json
                ├── $namespace$__productrelationship__c.json
                ├── $namespace$__promotion__c.json
                ├── $namespace$__promotionitem__c.json
                ├── $namespace$__rule__c.json
                ├── $namespace$__storyobjectconfiguration__c.json
                ├── $namespace$__timeplan__c.json
                ├── $namespace$__timepolicy__c.json
                ├── $namespace$__uifacet__c.json
                ├── $namespace$__uisection__c.json
                ├── $namespace$__vlocityaction__c.json
                ├── $namespace$__vlocityattachment__c.json
                ├── $namespace$__vlocitycard__c.json
                ├── $namespace$__vlocityfunction__c.json
                ├── $namespace$__vlocityfunctionargument__c.json
                ├── $namespace$__vlocitysearchwidgetactionssetup__c.json
                ├── $namespace$__vlocitysearchwidgetsetup__c.json
                ├── $namespace$__vlocitystate__c.json
                ├── $namespace$__vlocitystatemodel__c.json
                ├── $namespace$__vlocitystatemodelversion__c.json
                ├── $namespace$__vlocityuilayout__c.json
                ├── $namespace$__vlocityuitemplate__c.json
                ├── $namespace$__vqmachine__c.json
                ├── $namespace$__vqmachineresource__c.json
                ├── $namespace$__vqresource__c.json
                ├── document.json
                ├── pricebook2.json
                ├── pricebookentry.json
                ├── product2.json
                ├── recordtype.json
                └── user.json
        * Each of the object in the workset will have sobject with its fields which needs to be migrated as shown below
            * ```
              {
                    "objectname": "$namespace$__catalog__c",
                    "datafieldstomigrate": [
                        "name",
                        "$namespace$__catalogcode__c",
                        "$namespace$__description__c",
                        "$namespace$__enddatetime__c",
                        "$namespace$__globalkey__c",
                        "$namespace$__isactive__c",
                        "$namespace$__iscatalogroot__c",
                        "$namespace$__isdefault__c",
                        "$namespace$__sourcetype__c",
                        "$namespace$__startdatetime__c",
                        "nos_t_commname__c"
                    ],
                    "referencefields": [
                        {
                            "field": "$namespace$__defaultpricelistid__c",
                            "fieldobject": "$namespace$__pricelist__c",
                            "standard": false
                        }
                    ],
                    "childobjectstomigrate": [
                        {
                            "childsobject": "$namespace$__catalogproductrelationship__c",
                            "field": "$namespace$__catalogid__c"
                        },
                        {
                            "childsobject": "$namespace$__catalogrelationship__c",
                            "field": "$namespace$__childcatalogid__c"
                        },
                        {
                            "childsobject": "$namespace$__catalogrelationship__c",
                            "field": "$namespace$__parentcatalogid__c"
                        },
                        {
                            "childsobject": "$namespace$__promotionitem__c",
                            "field": "$namespace$__catalogcategoryid__c"
                        }
                    ]
                }```
        * To update list of fields needs to export , update “datafieldstomigrate”
        * To update list of referencefields fields needs to export , update “referencefields”
            * and if the reference field related object needs to be exported , please make sure to add export as true as shown below
                * ```
                  "referencefields": [
                            {
                                "field": "$namespace$__defaultpricelistid__c",
                                "fieldobject": "$namespace$__pricelist__c",
                                "standard": false,
                                "export" : true
                            }
                        ],```
        * To export/skip list of child objects, make sure “childobjectstomigrate” list is updated accordingly\
        * once done move 
            * from folder
                * object_configurations_workset
            * to folder
                * object_configurations
* Data Extraction:
    * in your code , open
        * data_migration_tool > sfdc > export_script.py
        * ```
             >>mig_script.py<<
            python3 export_script.py --object=product2 --ids=01t2o000007ZaFEAA0
            python3 export_script.py --object=vlocity_cmt__Attribute__c --ids=a1KKM000000KzQi2AK
            python3 export_script.py --object=vlocity_cmt__AttributeCategory__c --ids=a1JKN000000CcSR2A0```
    * update object name and ids or it can be automated using a query to extract object name and ids to be exported
    * in terminal , go to 
        * data_migration_tool > sfdc
    * execute following command to export all the data related 
        * python3 export_script.py
    * depending on the depth of the object relationships, it may take a while
    * once command execution is complete or while execution you should be able to see following logs along with object summary
        * ```
            querying product2 [========================================] 165/165 [100%] in 1.3s (128.02/s)
            querying pricebookentry [========================================] 314/314 [100%] in 0.3s (974.93/s)
            querying vlocity_cmt__pricelistentry__c [========================================] 1353/1353 [100%] in 1.8s (664.41/s)
            querying vlocity_cmt__pricingelement__c [========================================] 75/75 [100%] in 0.5s (142.71/s)
            querying vlocity_cmt__productchilditem__c [========================================] 0 in 0.3s (0.00/s)
            querying vlocity_cmt__productchilditem__c [========================================] 1678/1678 [100%] in 0.9s (1512.64/s)
            querying vlocity_cmt__pricelistentry__c [========================================] 500/500 [100%] in 0.9s (533.66/s)
            querying vlocity_cmt__pricelistentry__c [========================================] 500/500 [100%] in 0.8s (600.01/s)
            querying vlocity_cmt__pricelistentry__c [========================================] 500/500 [100%] in 0.8s (594.48/s)
            querying vlocity_cmt__pricelistentry__c [========================================] 500/500 [100%] in 0.9s (587.19/s)
            querying vlocity_cmt__pricelistentry__c [========================================] 500/500 [100%] in 0.9s (587.55/s)
            querying vlocity_cmt__pricelistentry__c [========================================] 125/125 [100%] in 0.5s (235.62/s)
            +----------------------------------+---------------------+
            |           Object Name            | Export Record Count |
            +----------------------------------+---------------------+
            |    $namespace$__promotion__c     |          1          |
            |            recordtype            |          4          |
            |     $namespace$__timeplan__c     |          2          |
            |    $namespace$__timepolicy__c    |          2          |
            |    $namespace$__pricelist__c     |          1          |
            |            pricebook2            |          1          |
            |  $namespace$__promotionitem__c   |         2625        |
            |             product2             |         659         |
            |   $namespace$__objectclass__c    |          6          |
            |          pricebookentry          |         1314        |
            |  $namespace$__pricelistentry__c  |        10715        |
            | $namespace$__productchilditem__c |         7025        |
            |  $namespace$__pricingelement__c  |         135         |
            +----------------------------------+---------------------+```
    * and also all the exported records will be now visible under
        * data_migration_tool > sfdc > results
        * ```
          ./results
            └── 2f54c928c256447dab3397cfee806948
                ├── $namespace$__objectclass__c
                │   ├── 1950789c2d6a42808c90bd351c95690c.json
                │   ├── 8a33d7d89ebd40a0bd575c99d3d660da.json
                │   └── b034b4f21399492c8f7d793c839b07b8.json
                ├── $namespace$__pricelist__c
                │   └── f75c113c13574aacb439110ffc9b709e.json
                ├── $namespace$__pricelistentry__c
                │   └── f64b9a23fae24457af0039706f1d11d2.json
                ├── $namespace$__pricingelement__c
                │   └── f13b0400ecc04e35b2469c8a1fc6cd5f.json
                ├── $namespace$__productchilditem__c
                │   ├── d78b2b1cc8cb414bb0df30f97aa61fc2.json
                │   └── fb6d0a60ae2d4dc28f261b236b47136b.json
                ├── $namespace$__promotion__c
                │   └── 11e5e1e5d89c414b906a64f895b2735d.json
                ├── $namespace$__promotionitem__c
                │   └── 2eda660b6b624936b9b7252a826622a6.json
                ├── $namespace$__timeplan__c
                │   ├── 369069836b994a62980aaf7a4f8e0796.json
                │   └── a62f7c7b87ac4b7183b2d0f9280eaa04.json
                ├── $namespace$__timepolicy__c
                │   ├── 6f0319b620874d09ad195fd3a508d3ce.json
                │   └── f3cab9c52deb4c1dae283b1cea6414bc.json
                ├── pricebook2
                │   └── 79b88c501f5048a7a6baa323e32955be.json
                ├── pricebookentry
                │   └── b1de40d5ba4a4cb8b0f478db833fbb5f.json
                ├── product2
                │   └── bb6ed3f9e9a2446894bc3853d99d8408.json
                └── recordtype
                    └── f98993d5fb064cb4b2f13d0861234374.json```
* Import Data:
    * in terminal , go to 
        * data_migration_tool > sfdc
    * execute following command to import all the data which was migrated before
        * python3 import_script.py
* Error Handling and Logging:
    * #to be updated
* Post-Migration Validation:
    * #to be updated
* Security & Permissions:
    * #to be updated
* Scalability:
    * #to be updated



