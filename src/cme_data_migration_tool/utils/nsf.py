class nsf():

    @staticmethod
    def mask(orgconfig, stringdata):
        return stringdata.replace(orgconfig.namespace, "$namespace$").lower()
    
    @staticmethod
    def unmask(orgconfig, stringdata):
        return stringdata.replace("$namespace$", orgconfig.namespace).lower()
    
    @staticmethod
    def robject(field):
        return nsf.replace_last(field, "__c", "__r") if field.endswith("__c") else nsf.replace_last(field, "id", "")

    @staticmethod
    def replace_last(source_string, replace_what, replace_with):
        head, _sep, tail = source_string.rpartition(replace_what)
        return head + replace_with + tail
    
    @staticmethod
    def cleanup(source_string):
        result = nsf.replace_last(source_string, "__c", "")
        result = nsf.replace_last(result, "__r", "")
        result = result.replace("$namespace$__", "").lower()
        return result