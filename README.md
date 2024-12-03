# CME Data Migration Tool

CME Data Migration tool is designed to efficiently transfer data from one Salesforce org to another with CME data. The tool aims to streamline the migration process by ensuring accurate data mapping, maintaining record relationships, and adhering to Salesforce's API and governor limits. It facilitates data migration across standard and custom objects, while preserving data integrity, security, and field-level permissions. The migration tool is designed to handle large data volumes through optimized batching and bulk API usage, with built-in error logging, retry mechanisms, and post-migration validation to ensure data consistency. By addressing key challenges like heap size limitations, API call limits, and data dependencies, the tool provides a robust solution for seamless Salesforce org-to-org data transfers.

## Features
   - Export Data: Export data from a source Salesforce org.
   - Import Data: Import data into a destination Salesforce org.
   - Describe Metadata: Describe the metadata of source and destination orgs.
   - Validation Options: Optionally suppress validation checks during migration.

## Tech
CME Data Migration tool is a python based tool which requires [python 3][python3 documentation]

## Installation
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

## Script Structure

```
./data_migration_tool
└── configurations
│  ├── epc_customs_configurations.json 
│  ├── source_org.json  // to  setup source org credentialds
│  └── destination_org.json / to  setup destination org credentialds
└── dmt.py
```

## Setup Org Credentials
 - edit cme_data_migration_tool > configurations > source_org.json to update source org credentials
 - edit cme_data_migration_tool > configurations > destination_org.json to update destination org credentials
 - working org json configuration would require
 -- username
 -- password
 -- consumer_key
 -- consumer_secret
 -- domain(production/test)
 -- instance_url
 -- namespace
- sample org json config can be referred below

```
{
  "username": "admin@cxo.com",
  "password": "password",
  "consumer_key": "key***",
  "consumer_secret": "secret***",
  "domain": "test",
  "instance_url": "https://cxo-dev-ed.develop.my.salesforce-com.nbollimpalli-extvgacqz6ch1.wc.crm.dev",
  "namespace": "vlocity_cmt"
}
```

## Usage

CME Data Migration tool can be used to export/import by running following commands

```
usage: dmt.py [-h] [-iv {metadata}] [--resultpath RESULTPATH] {export,import,describe} ...

positional arguments:
  {export,import,describe}
                        commands
    export              sub command to export data from source org
    import              sub command to import data to destination org
    describe            sub command to describe source and destination org metadata

options:
  -h, --help            show this help message and exit
  -iv, --ignorevalidations {metadata}
                        This setting will suppress validations
  --resultpath RESULTPATH
                        specify the path where results are required to be exported or imported from and path has to be absolute path in your file system
```

```
usage: dmt.py export [-h] [--config {default,sobject}] --object OBJECT --ids IDS

options:
  -h, --help            show this help message and exit
  --config {default,sobject}
                        This flag will include related child records if config is default , single sobject if config value is sobject, if this option is not provided default value will be default
  --object OBJECT       Specify the object to export currently we support only Product2 or Promotion for config type default, all EPC objects for config type sobject
  --ids IDS             Ids of the object type to export, currently we support only one id for current release
```

```
usage: dmt.py import [-h] [-f IMPORTFILE]

options:
  -h, --help            show this help message and exit
  -f, --importfile IMPORTFILE
                        specify the path where import results are required to be stored and path has to be absolute path in your file system
```

```
usage: dmt.py describe [-h]

options:
  -h, --help  show this help message and exit
```

### Examples
 - To export single sobject
 -- ``` python3 dmt.py export --object=product2 --ids=01txx0000006i8uAAA --config=sobject```
 - To export sobject with its related records
 -- ``` python3 dmt.py export --object=product2 --ids=01txx0000006i8uAAA```
 - To import
 -- ```python3 dmt.py import --importfile=epc_import_args_sample```

## License
Apache License Version 2.0

### open source packages used
- [Simple Salesforce]
- [about-time]
- [alive-progress]
- [prettytable]

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [python3 documentation]: <https://docs.python.org/3/>
   [Simple Salesforce]: <https://github.com/simple-salesforce/simple-salesforce>
   [about-time]: <https://github.com/rsalmei/about-time>
   [alive-progress]: <https://github.com/rsalmei/alive-progress>
   [prettytable]: <>