from typing import List, Dict, Any

class CalculationBuilder:

    def __init__(self, results) -> None:
        self.results = results

    def build_node(self) -> Dict[str, Any]:
        return {"CalculationMatrix": self._build_calculation_matrix_node(),
            "CalculationProcedure": self._build_calculation_procedure_node(),
            "CpqConfigurationSetup": self._build_cpq_configuration_setup_node()}
    
    def _build_calculation_matrix_node(self) -> Dict[str, Any]:
        all_calculation_matrices_map = {r.get("Id"): r for r in self.results.get("CalculationMatrix")}
        calculation_matrix_nodes = []
        for calculation_matrix in all_calculation_matrices_map.values():
            children: Dict[str, Any] = {}
            children["CalculationMatrixVersion"] = self._build_calculation_matrix_version_node(calculation_matrix.get("Id"))
            calculation_matrix_nodes.append({"entity": "CalculationMatrix", "record": calculation_matrix, "children": children})
        return calculation_matrix_nodes

    def _build_calculation_matrix_version_node(self, calculation_matrix_id: str) -> Dict[str, Any]:
        all_calculation_matrix_versions_map = {r.get("Id"): r for r in self.results.get("CalculationMatrixVersion")}
        calculation_matrix_version_nodes = []
        for calculation_matrix_version in all_calculation_matrix_versions_map.values():
            if calculation_matrix_version.get("vlocity_cmt__CalculationMatrixId__c") == calculation_matrix_id:
                children: Dict[str, Any] = {}
                children["CalculationMatrixRow"] = self._build_calculation_matrix_row_node(calculation_matrix_version.get("Id"))
                calculation_matrix_version_nodes.append({"entity": "CalculationMatrixVersion", "record": calculation_matrix_version, "children": children})
        return calculation_matrix_version_nodes

    def _build_calculation_matrix_row_node(self, calculation_matrix_version_id: str) -> Dict[str, Any]:
        all_calculation_matrix_rows_map = {r.get("Id"): r for r in self.results.get("CalculationMatrixRow")}
        calculation_matrix_row_nodes = []
        for calculation_matrix_row in all_calculation_matrix_rows_map.values():
            if calculation_matrix_row.get("vlocity_cmt__CalculationMatrixVersionId__c") == calculation_matrix_version_id:
                calculation_matrix_row_nodes.append({"entity": "CalculationMatrixRow", "record": calculation_matrix_row})
        return calculation_matrix_row_nodes

    def _build_calculation_procedure_node(self) -> Dict[str, Any]:
        all_calculation_procedures_map = {r.get("Id"): r for r in self.results.get("CalculationProcedure")}
        calculation_procedure_nodes = []
        for calculation_procedure in all_calculation_procedures_map.values():
            children: Dict[str, Any] = {}
            children["CalculationProcedureVersion"] = self._build_calculation_procedure_version_node(calculation_procedure.get("Id"))
            calculation_procedure_nodes.append({"entity": "CalculationProcedure", "record": calculation_procedure, "children": children})
        return calculation_procedure_nodes

    def _build_calculation_procedure_version_node(self, calculation_procedure_id: str) -> Dict[str, Any]:
        all_calculation_procedure_versions_map = {r.get("Id"): r for r in self.results.get("CalculationProcedureVersion")}
        calculation_procedure_version_nodes = []
        for calculation_procedure_version in all_calculation_procedure_versions_map.values():
            if calculation_procedure_version.get("vlocity_cmt__CalculationProcedureId__c") == calculation_procedure_id:
                children: Dict[str, Any] = {}
                children["CalculationProcedureStep"] = self._build_calculation_procedure_step_node(calculation_procedure_version.get("Id"))
                calculation_procedure_version_nodes.append({"entity": "CalculationProcedureVersion", "record": calculation_procedure_version, "children": children})
        return calculation_procedure_version_nodes

    def _build_calculation_procedure_step_node(self, calculation_procedure_version_id: str) -> Dict[str, Any]:
        all_calculation_procedure_steps_map = {r.get("Id"): r for r in self.results.get("CalculationProcedureStep")}
        calculation_procedure_step_nodes = []
        for calculation_procedure_step in all_calculation_procedure_steps_map.values():
            if calculation_procedure_step.get("vlocity_cmt__CalculationProcedureVersionId__c") == calculation_procedure_version_id:
                calculation_procedure_step_nodes.append({"entity": "CalculationProcedureStep", "record": calculation_procedure_step})
        return calculation_procedure_step_nodes

    def _build_cpq_configuration_setup_node(self) -> Dict[str, Any]:
        all_cpq_configuration_setups_map = {r.get("Id"): r for r in self.results.get("CpqConfigurationSetup")}
        cpq_configuration_setup_nodes = []
        for cpq_configuration_setup in all_cpq_configuration_setups_map.values():
            cpq_configuration_setup_nodes.append({"entity": "CpqConfigurationSetup", "record": cpq_configuration_setup})
        return cpq_configuration_setup_nodes