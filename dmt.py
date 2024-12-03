import argparse

from src.cme_data_migration_tool.actions.action_factory import ActionFactory

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("-iv", "--ignorevalidations", help="This setting will suppress validations", choices=["metadata"], default = "default")
    parser.add_argument("--resultpath", help="specify the path where results are required to be exported or imported from and path has to be absolute path in your file system", type=str, default = None)

    sub_parsers = parser.add_subparsers(help='commands', dest="operation")
    export_parser = sub_parsers.add_parser("export", help='sub command to export data from source org')
    import_parser = sub_parsers.add_parser("import", help='sub command to import data to destination org')
    sub_parsers.add_parser("describe", help='sub command to describe source and destination org metadata')

    export_parser.add_argument("--config", help="This flag will include related child records if config is default , single sobject if config value is sobject, if this option is not provided default value will be default", choices=["default", "sobject"], default = "default")
    export_parser.add_argument("--object", help="Specify the object to export currently we support only Product2 or Promotion for config type default, all EPC objects for config type sobject", type=str, default = None, required=True)
    export_parser.add_argument("--ids", help=" Ids of the object type to export, currently we support only one id for current release", type=lambda arg: arg.split(','), default = None, required=True)

    import_parser.add_argument("-f", "--importfile", help="specify the path where import results are required to be stored and path has to be absolute path in your file system", type=str, default = None)

    args = parser.parse_args()

    ActionFactory.getinstance().create_action(args).execute_action()

if __name__ == '__main__':
    main()
