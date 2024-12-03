from src.cme_data_migration_tool.actions.base_action import BaseAction
from src.cme_data_migration_tool.actions.describe_action import DescribeAction
from src.cme_data_migration_tool.actions.export_action import ExportAction
from src.cme_data_migration_tool.actions.import_action import ImportAction


class ActionFactory:
    action_factory_instance = None
    
    @staticmethod
    def getinstance():
        if ActionFactory.action_factory_instance is None:
            ActionFactory.action_factory_instance = ActionFactory()
        return ActionFactory.action_factory_instance

    def create_action(self, args) -> BaseAction:
        if args.operation == "import":
            return ImportAction(args)
        elif args.operation == "export":
            return ExportAction(args)
        elif args.operation == "describe":
            return DescribeAction(args)
        else:
            raise ValueError(f"Unknown action type: {args.operation}")