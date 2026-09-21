import json,os,uuid
from alive_progress import alive_bar
from src.cme_data_migration_tool.dtos.configurations_dtos.org_config_dto import OrgConfigDTO
from src.cme_data_migration_tool.dtos.runtime_dtos.global_results_dto import GlobalResultsDTO
from src.cme_data_migration_tool.services.export_service import ExportService
from src.cme_data_migration_tool.services.export_bundle import ExportBundle
from src.cme_data_migration_tool.utils.nsf import nsf

class ExportCatalog():
    def __init__(self):
        self.orgconfig = OrgConfigDTO.getsourceorg()
        self.finalcatalogids = set()
        self.finalcatalogrelationshipids = set()
        self.finalcprids = set()
        self.finalproductids = set()
        self.finalpromotionids = set()
        self.finalpromotionitemids = set()
        return None

    def savefile(self, fpath, result, resultname):
        with alive_bar(1, bar = 'classic', title="saving results of "+resultname) as bar:
            if os.path.isfile(fpath):
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

    def getlinkedcatalogids(self, catalogids):
        objectidsstring = ",".join("'" + objectid + "'" for objectid in catalogids)
        catalogrelobj = nsf.unmask(self.orgconfig, "$namespace$__catalogrelationship__c")
        childfield = nsf.unmask(self.orgconfig, "$namespace$__childcatalogid__c")
        parentfield = nsf.unmask(self.orgconfig, "$namespace$__parentcatalogid__c")
        querystring = "SELECT Id, {1}, {2} FROM {0} WHERE {2} IN ({3}) OR {1} IN ({3})".format(catalogrelobj, childfield, parentfield, objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__(catalogrelobj).query(querystring, lazy_operation=True)
        newcatalogids = set()
        for list_results in fetch_results:
            for raw_result in list_results:
                result = nsf.lowerkeys(raw_result)
                if result['id'] is not None:
                    self.finalcatalogrelationshipids.add(result['id'])
                for catalogfield in (childfield, parentfield):
                    catalogid = result[catalogfield]
                    if catalogid is not None and catalogid not in self.finalcatalogids:
                        newcatalogids.add(catalogid)
        return newcatalogids

    def resolveallcatalogs(self, rootcatalogids):
        self.finalcatalogids.update(rootcatalogids)
        pendingcatalogids = set(rootcatalogids)
        while len(pendingcatalogids) > 0:
            newcatalogids = self.getlinkedcatalogids(list(pendingcatalogids))
            newcatalogids -= self.finalcatalogids
            self.finalcatalogids.update(newcatalogids)
            pendingcatalogids = newcatalogids

    def getallcpr(self):
        if len(self.finalcatalogids) == 0:
            return None
        objectidsstring = ",".join("'" + objectid + "'" for objectid in self.finalcatalogids)
        cprobj = nsf.unmask(self.orgconfig, "$namespace$__catalogproductrelationship__c")
        productfield = nsf.unmask(self.orgconfig, "$namespace$__product2id__c")
        promotionfield = nsf.unmask(self.orgconfig, "$namespace$__promotionid__c")
        catalogfield = nsf.unmask(self.orgconfig, "$namespace$__catalogid__c")
        querystring = "SELECT Id, {1}, {2} FROM {0} WHERE {3} IN ({4})".format(cprobj, productfield, promotionfield, catalogfield, objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__(cprobj).query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for raw_result in list_results:
                result = nsf.lowerkeys(raw_result)
                if result['id'] is not None:
                    self.finalcprids.add(result['id'])
                if result[productfield] is not None:
                    self.finalproductids.add(result[productfield])
                if result[promotionfield] is not None:
                    self.finalpromotionids.add(result[promotionfield])
        return None

    def getallpromotionitems(self):
        if len(self.finalpromotionids) == 0:
            return None
        objectidsstring = ",".join("'" + objectid + "'" for objectid in self.finalpromotionids)
        promotionitemobj = nsf.unmask(self.orgconfig, "$namespace$__promotionitem__c")
        promotionfield = nsf.unmask(self.orgconfig, "$namespace$__promotionid__c")
        querystring = "SELECT Id FROM {0} WHERE {1} IN ({2})".format(promotionitemobj, promotionfield, objectidsstring)
        fetch_results = self.orgconfig.org_connector.bulk.__getattr__(promotionitemobj).query(querystring, lazy_operation=True)
        for list_results in fetch_results:
            for raw_result in list_results:
                result = nsf.lowerkeys(raw_result)
                if result['id'] is not None:
                    self.finalpromotionitemids.add(result['id'])
        return None

    def export_promotions(self, promotionids):
        if len(promotionids) == 0:
            return None
        self.finalpromotionids.update(promotionids)
        self.finalexport(list(self.finalpromotionids), "$namespace$__promotion__c")
        self.getallpromotionitems()
        self.finalexport(list(self.finalpromotionitemids), "$namespace$__promotionitem__c")

    def export(self, object, catalogids):
        if len(catalogids) == 0:
            return None

        print('resolving linked catalogs, please wait while we start exporting, this may take few seconds')
        self.resolveallcatalogs(catalogids)
        self.finalexport(list(self.finalcatalogids), "$namespace$__catalog__c")
        self.finalexport(list(self.finalcatalogrelationshipids), "$namespace$__catalogrelationship__c")

        print('resolving products and promotions attached to the catalog, please wait while we start exporting, this may take few seconds')
        self.getallcpr()
        self.finalexport(list(self.finalcprids), "$namespace$__catalogproductrelationship__c")

        if len(self.finalproductids) > 0:
            print('prepping data to export for products attached to the catalog, please wait while we start exporting, this may take few seconds')
            ExportBundle().export("product2", list(self.finalproductids), save_results=False)

        if len(self.finalpromotionids) > 0:
            print('prepping data to export for promotions attached to the catalog, please wait while we start exporting, this may take few seconds')
            self.export_promotions(list(self.finalpromotionids))

        self.savefile('./results/'+ 'epc_import_args_'+str(uuid.uuid4())+'.json' , GlobalResultsDTO.globalobjectimportfileinfomap, 'import configurations')
