import json,os,uuid
from alive_progress import alive_bar
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO
from src.cme_data_migration_tool.services.export_service import ExportService
from src.cme_data_migration_tool.utils.nsf import nsf

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
        pciobj = nsf.unmask(self.orgconfig, "$namespace$__productchilditem__c")
        parentfield = nsf.unmask(self.orgconfig, "$namespace$__parentproductid__c")
        parentreffield = nsf.unmask(self.orgconfig, "$namespace$__parentproductid__r")
        objecttypefield = nsf.unmask(self.orgconfig, "$namespace$__objecttypeid__c")
        childfield = nsf.unmask(self.orgconfig, "$namespace$__childproductid__c")
        childreffield = nsf.unmask(self.orgconfig, "$namespace$__childproductid__r")
        globalkeyfield = nsf.unmask(self.orgconfig, "$namespace$__globalkey__c")
        querystring = "SELECT Id, {1}, {2}.{3}, {2}.RecordTypeId, {4}, {5}.{6} FROM {0} WHERE {1} in ({7})".format(
            pciobj, parentfield, parentreffield, objecttypefield, childfield, childreffield, globalkeyfield, objectidsstring)
        # data = orgconfig.org_connector.query_all_iter(querystring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__(pciobj).query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for raw_result in list_results :
                result = nsf.lowerkeys(raw_result)
                self.finalpciids.append(result['id'])
                parent_product = result[parentreffield]
                if parent_product != None:
                    recordtypeid = parent_product['recordtypeid']
                    objectclassid = parent_product[objecttypefield]
                    self.finalobjectclassids.add(objectclassid) if objectclassid is not None else None
                    self.finalrecorditypeds.add(recordtypeid) if recordtypeid is not None else None
                if result[childfield] != None:
                    product_ids.append(result[childfield])

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
        attrassignobj = nsf.unmask(self.orgconfig, "$namespace$__attributeassignment__c")
        attrcatfield = nsf.unmask(self.orgconfig, "$namespace$__attributecategoryid__c")
        attrfield = nsf.unmask(self.orgconfig, "$namespace$__attributeid__c")
        objectfield = nsf.unmask(self.orgconfig, "$namespace$__objectid__c")
        querystring = "SELECT Id,{1},{2} FROM {0} WHERE {3} in ({4})".format(attrassignobj, attrcatfield, attrfield, objectfield, objectidsstring)
        # data = orgconfig.org_connector.query_all_iter(querystring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__(attrassignobj).query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for raw_result in list_results :
                result = nsf.lowerkeys(raw_result)
                if result['id'] != None:
                    self.finalattrassignids.add(result['id'])
                if result[attrcatfield] != None:
                    self.finalattrcatids.add(result[attrcatfield])
                if result[attrfield] != None:
                    self.finalattrids.add(result[attrfield])
        return None

    def getallcompiledoverrides(self):
        if len(self.finalprodids) == 0:
            return None
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in self.finalprodids)
        overridedefobj = nsf.unmask(self.orgconfig, "$namespace$__overridedefinition__c")
        compiledattrfield = nsf.unmask(self.orgconfig, "$namespace$__compiledattributeoverrideid__c")
        productfield = nsf.unmask(self.orgconfig, "$namespace$__productid__c")
        querystring = "SELECT {1}, Id FROM {0} WHERE {2} in ({3})".format(overridedefobj, compiledattrfield, productfield, objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__(overridedefobj).query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for raw_result in list_results :
                result = nsf.lowerkeys(raw_result)
                if result['id'] != None:
                    self.finaloverridedefs.add(result['id'])
                if result[compiledattrfield] != None:
                    self.finalcompiledattrids.add(result[compiledattrfield])
        return None

    def getallples(self):
        if len(self.finalprodids) == 0:
            return None
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in self.finalprodids)
        pleobj = nsf.unmask(self.orgconfig, "$namespace$__pricelistentry__c")
        pefield = nsf.unmask(self.orgconfig, "$namespace$__pricingelementid__c")
        pereffield = nsf.unmask(self.orgconfig, "$namespace$__pricingelementid__r")
        pvfield = nsf.unmask(self.orgconfig, "$namespace$__pricingvariableid__c")
        pbefield = nsf.unmask(self.orgconfig, "$namespace$__pricebookentryid__c")
        plfield = nsf.unmask(self.orgconfig, "$namespace$__pricelistid__c")
        productfield = nsf.unmask(self.orgconfig, "$namespace$__productid__c")
        objecttypefield = nsf.unmask(self.orgconfig, "$namespace$__objecttypeid__c")
        querystring = "SELECT Id, {1}, {2}.{3}, {2}.{8}, {4}, {5} FROM {0} WHERE {6} in ({7})".format(
            pleobj, pefield, pereffield, pvfield, pbefield, plfield, productfield, objectidsstring, objecttypefield)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__(pleobj).query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for raw_result in list_results :
                result = nsf.lowerkeys(raw_result)
                if result['id'] != None:
                    self.finalpleids.add(result['id'])
                if result[pbefield] != None:
                    self.finalpbeids.add(result[pbefield])
                if result[pefield] != None:
                    self.finalpeids.add(result[pefield])
                if result[plfield] != None:
                    self.finalplids.add(result[plfield])
                if result[pereffield] != None and result[pereffield][pvfield] != None:
                    self.finalpvids.add(result[pereffield][pvfield])
                if result[pereffield] != None and result[pereffield][objecttypefield] != None:
                    self.finalobjectclassids.add(result[pereffield][objecttypefield])
        return None
    
    def getallpricebooks(self):
        if len(self.finalpbeids) == 0:
            return None
        objectidsstring = ",".join("'" + objectid + "'" for objectid in self.finalpbeids)
        querystring = "SELECT Id, Pricebook2Id FROM PricebookEntry WHERE Id in ({0})".format(objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__("PricebookEntry").query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for raw_result in list_results:
                result = nsf.lowerkeys(raw_result)
                if result['pricebook2id'] != None:
                    self.finalpbids.add(result['pricebook2id'])
        return None

    def getAllCPR(self):
        if len(self.finalprodids) == 0:
            return None
        objectidsstring =  ",".join("'" + objectid + "'" for objectid in self.finalprodids)
        cprobj = nsf.unmask(self.orgconfig, "$namespace$__catalogproductrelationship__c")
        catalogfield = nsf.unmask(self.orgconfig, "$namespace$__catalogid__c")
        productfield = nsf.unmask(self.orgconfig, "$namespace$__product2id__c")
        fieldlist = ",".join([
            "Id", catalogfield,
            nsf.unmask(self.orgconfig, "$namespace$__effectivedate__c"),
            nsf.unmask(self.orgconfig, "$namespace$__enddate__c"),
            nsf.unmask(self.orgconfig, "$namespace$__isactive__c"),
            nsf.unmask(self.orgconfig, "$namespace$__itemtype__c"),
            nsf.unmask(self.orgconfig, "$namespace$__productgroupkey__c"),
            nsf.unmask(self.orgconfig, "$namespace$__promotionid__c"),
            nsf.unmask(self.orgconfig, "$namespace$__sequencenumber__c"),
        ])
        querystring = "SELECT {1} FROM {0} WHERE {2} IN ({3})".format(cprobj, fieldlist, productfield, objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__(cprobj).query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for raw_result in list_results:
                result = nsf.lowerkeys(raw_result)
                if result['id'] != None:
                    self.finalcprids.add(result['id'])
                if result[catalogfield] != None:
                    self.finalcatalogids.add(result[catalogfield])

        return None
    
    def export(self, object, productid, save_results=True):
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
        self.getallpricebooks()
        self.finalexport(list(self.finalpbids), "pricebook2")
        self.finalexport(list(self.finalpbeids), "pricebookentry")
        # finalexport(list(finalrecorditypeds), "recordtype")
        self.finalexport(list(self.finalobjectclassids), "$namespace$__objectclass__c")

        if save_results:
            self.savefile('./results/'+ 'epc_import_args_'+str(uuid.uuid4())+'.json' , GlobalResultsDTO.globalobjectimportfileinfomap, 'import configurations')