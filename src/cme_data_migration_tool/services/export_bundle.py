import json,os,uuid
from alive_progress import alive_bar
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO
from src.cme_data_migration_tool.services.export_service import ExportService

class ExportBundle():
    def __init__(self):
        self.orgconfig = OrgConfigDTO.getsourceorg()
        self.finalobjectclassids = set()
        self.finalrecorditypeds = set()
        self.finalpciids = []
        self.finalprodids = []
        self.finalattrassignids = set()
        self.finalattrids = set()
        self.finalattrcatids = set()
        self.finalcompiledattrids = set()
        self.finaloverridedefs = set()
        self.finalpleids = set()
        self.finalplids = set()
        self.finalpbeids = set()
        self.finalpbids = set()
        self.finalpeids = set()
        self.finalpvids = set()
        self.finalcprids = set()
        self.finalcatalogids = set()
        self.product_id_to_global_key = {}
        return None

    def savefile(self, fpath, result, resultname):
            with alive_bar(1, bar = 'classic', title="saving results of "+resultname) as bar:
                if os.path.isfile(fpath) :
                    os.remove(fpath)
                with open(fpath, 'w') as f:
                    json.dump(result, f)
                bar()

    def finalexport(self, objectids, objname):
        if len(objectids) > 0:
            for i in range(0, len(objectids), 200):
                objectids_to_export_chunk = objectids[i:i + 200]
                exportservice = ExportService(True, objname, objname, 'id', objectids_to_export_chunk)
                exportservice.export()

    def getallproductidsinhierarchy(self, productids):
        if len(productids) == 0:
            return None
        product_ids = []
        
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in productids)
        querystring = "SELECT Id, vlocity_cmt__ParentProductId__c, vlocity_cmt__ParentProductId__r.vlocity_cmt__ObjectTypeId__c, vlocity_cmt__ParentProductId__r.RecordTypeId, vlocity_cmt__ChildProductId__c, vlocity_cmt__ChildProductId__r.vlocity_cmt__GlobalKey__c FROM vlocity_cmt__ProductChildItem__c WHERE vlocity_cmt__ParentProductId__c in ({})".format(objectidsstring)
        # data = orgconfig.org_connector.query_all_iter(querystring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__('vlocity_cmt__ProductChildItem__c').query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for result in list_results :
                self.finalpciids.append(result['Id'])
                parent_product = result['vlocity_cmt__ParentProductId__r']
                if parent_product != None:
                    recordtypeid = parent_product['RecordTypeId']
                    objectclassid = parent_product['vlocity_cmt__ObjectTypeId__c']
                    self.finalobjectclassids.add(objectclassid) if objectclassid is not None else None
                    self.finalrecorditypeds.add(recordtypeid) if recordtypeid is not None else None
                if result['vlocity_cmt__ChildProductId__c'] != None:
                    product_ids.append(result['vlocity_cmt__ChildProductId__c'])

        product_ids = list(set(product_ids))
        self.finalprodids.extend(product_ids)

        if(len(product_ids) > 0):
            self.getallproductidsinhierarchy(product_ids)
        return None

    def getallattributeassignments(self):
        object_to_query = []
        object_to_query.extend(self.finalprodids)
        object_to_query.extend(self.finalobjectclassids)
        if len(object_to_query) == 0:
            return None
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in object_to_query)
        querystring = "SELECT Id,vlocity_cmt__AttributeCategoryId__c,vlocity_cmt__AttributeId__c FROM vlocity_cmt__AttributeAssignment__c WHERE vlocity_cmt__ObjectId__c in ({})".format(objectidsstring)
        # data = orgconfig.org_connector.query_all_iter(querystring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__('vlocity_cmt__AttributeAssignment__c').query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for result in list_results :
                if result['Id'] != None:
                    self.finalattrassignids.add(result['Id'])
                if result['vlocity_cmt__AttributeCategoryId__c'] != None:
                    self.finalattrcatids.add(result['vlocity_cmt__AttributeCategoryId__c'])
                if result['vlocity_cmt__AttributeId__c'] != None:
                    self.finalattrids.add(result['vlocity_cmt__AttributeId__c'])
        return None

    def getallcompiledoverrides(self):
        if len(self.finalprodids) == 0:
            return None
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in self.finalprodids)
        querystring = "SELECT vlocity_cmt__CompiledAttributeOverrideId__c, Id FROM vlocity_cmt__OverrideDefinition__c WHERE vlocity_cmt__ProductId__c in ({})".format(objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__('vlocity_cmt__OverrideDefinition__c').query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for result in list_results :
                if result['Id'] != None:
                    self.finaloverridedefs.add(result['Id'])
                if result['vlocity_cmt__CompiledAttributeOverrideId__c'] != None:
                    self.finalcompiledattrids.add(result['vlocity_cmt__CompiledAttributeOverrideId__c'])
        return None

    def getallples(self):
        if len(self.finalprodids) == 0:
            return None
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in self.finalprodids)
        querystring = "SELECT Id, vlocity_cmt__PricingElementId__c, vlocity_cmt__PricingElementId__r.vlocity_cmt__PricingVariableId__c, vlocity_cmt__PriceBookEntryId__c, vlocity_cmt__PriceListId__c FROM vlocity_cmt__PriceListEntry__c WHERE vlocity_cmt__ProductId__c in ({})".format(objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__('vlocity_cmt__PriceListEntry__c').query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for result in list_results :
                if result['Id'] != None:
                    self.finalpleids.add(result['Id'])
                if result['vlocity_cmt__PriceBookEntryId__c'] != None:
                    self.finalpbeids.add(result['vlocity_cmt__PriceBookEntryId__c'])
                if result['vlocity_cmt__PricingElementId__c'] != None:
                    self.finalpeids.add(result['vlocity_cmt__PricingElementId__c'])
                if result['vlocity_cmt__PriceListId__c'] != None:
                    self.finalplids.add(result['vlocity_cmt__PriceListId__c'])
                if result['vlocity_cmt__PricingElementId__r'] != None and result['vlocity_cmt__PricingElementId__r']['vlocity_cmt__PricingVariableId__c'] != None:
                    self.finalpvids.add(result['vlocity_cmt__PricingElementId__r']['vlocity_cmt__PricingVariableId__c'])
        return None
    
    def getAllCPR(self):
        if len(self.finalprodids) == 0:
            return None
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in self.finalprodids)
        querystring = "SELECT Id, vlocity_cmt__CatalogId__c, vlocity_cmt__EffectiveDate__c, vlocity_cmt__EndDate__c, vlocity_cmt__IsActive__c, vlocity_cmt__ItemType__c, vlocity_cmt__ProductGroupKey__c, vlocity_cmt__PromotionId__c, vlocity_cmt__SequenceNumber__c FROM vlocity_cmt__CatalogProductRelationship__c WHERE vlocity_cmt__Product2Id__c IN ({})".format(objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__('vlocity_cmt__CatalogProductRelationship__c').query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for result in list_results:
                if result['Id'] != None:
                    self.finalcprids.add(result['Id'])
                if result['vlocity_cmt__CatalogId__c'] != None:
                    self.finalcatalogids.add(result['vlocity_cmt__CatalogId__c'])
                
        return None
    
    def export(self, object, productid):
        if len(productid) == 0:
            return None
        print('prepping data to export for pcis, products, please wait while we start exporting , this may take few seconds')
        self.getallproductidsinhierarchy(productid)
        self.finalprodids.extend(productid)
        self.finalexport(self.finalprodids, "product2")
        
        print('prepping data to export for catalog product relationship info, please wait while we start exporting , this may take few seconds')
        self.getAllCPR()
        self.finalexport(list(self.finalcprids), "$namespace$__catalogproductrelationship__c")
        
        self.finalexport(self.finalpciids, "$namespace$__productchilditem__c")
        self.finalpciids = []

        print('prepping data to export for attribute assignments, attribtues, categories, please wait while we start exporting , this may take few seconds')
        self.getallattributeassignments()

        self.finalexport(list(self.finalattrcatids), "$namespace$__attributecategory__c")
        self.finalexport(list(self.finalattrids), "$namespace$__attribute__c")
        self.finalexport(list(self.finalattrassignids), "$namespace$__attributeassignment__c")

        print('prepping data to export for compiled overrides, override definitions, please wait while we start exporting , this may take few seconds')
        self.getallcompiledoverrides()
        self.finalexport(list(self.finaloverridedefs), "$namespace$__overridedefinition__c")
        self.finalexport(list(self.finalcompiledattrids), "$namespace$__compiledattributeoverride__c")

        print('prepping data to export for pricing info, please wait while we start exporting , this may take few seconds')
        self.getallples()
        self.finalexport(list(self.finalplids), "$namespace$__pricelist__c")
        self.finalexport(list(self.finalpleids), "$namespace$__pricelistentry__c")
        self.finalexport(list(self.finalpeids), "$namespace$__pricingelement__c")
        self.finalexport(list(self.finalpvids), "$namespace$__pricingvariable__c")
        self.finalexport(list(self.finalpbeids), "pricebookentry")
        # finalexport(list(finalrecorditypeds), "recordtype")
        self.finalexport(list(self.finalobjectclassids), "$namespace$__objectclass__c")

        self.savefile('./results/'+ 'epc_import_args_'+str(uuid.uuid4())+'.json' , GlobalResultsDTO.globalobjectimportfileinfomap, 'import configurations')