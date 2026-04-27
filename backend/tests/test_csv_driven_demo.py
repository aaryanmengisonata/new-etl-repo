import pytest
import allure
import pandas as pd
import re
from typing import Dict, List, Any
from utils.sqlite_client import SQLiteClient

@allure.epic("ETL Testing Framework")
@allure.feature("CSV-Driven ETL Validation Demo")
class TestCSVDrivenDemo:
    """CSV-Driven ETL Validation Demo - Works with SQLite"""
    
    @classmethod
    def setup_class(cls):
        """Setup database client and load CSV tests"""
        cls.db_client = SQLiteClient()
        cls.test_cases = cls._load_test_cases()
    
    @classmethod
    def _load_test_cases(cls) -> List[Dict]:
        """Load test cases from CSV"""
        csv_file = "data/etl_validation_demo.csv"
        df = pd.read_csv(csv_file)
        df['enabled'] = df['enabled'].astype(str)
        enabled_df = df[df['enabled'].str.upper() == 'TRUE']
        return enabled_df.to_dict('records')
    
    @staticmethod
    def _execute_query_with_variables(client, query: str, variables: Dict[str, Any]) -> Any:
        """Execute query with variable substitution"""
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in query:
                if isinstance(var_value, list):
                    var_value = ','.join(map(str, var_value))
                query = query.replace(placeholder, str(var_value))
        return client.execute_query(query)
    
    @staticmethod
    def _extract_variables_from_query(query: str) -> List[str]:
        """Extract variable names from query"""
        return re.findall(r'\{(\w+)\}', query)
    
    def _execute_validation(self, test_case: Dict) -> Dict[str, Any]:
        """Execute validation based on test case"""
        
        test_id = test_case['test_id']
        source_query = test_case['source_query']
        target_query = test_case['target_query']
        validation_type = test_case['validation_type']
        
        with allure.step(f"Execute source query for {test_id}"):
            source_variables = {}
            target_vars = self._extract_variables_from_query(target_query)
            
            source_results = self.db_client.execute_query(source_query)
            allure.attach(str(source_results[:10]), name='Source Query Results', 
                         attachment_type=allure.attachment_type.TEXT)
            
            if 'recid_list' in target_vars:
                recid_list = [row['recid'] for row in source_results]
                source_variables['recid_list'] = recid_list
                allure.attach(str(recid_list), name='RecID List', 
                             attachment_type=allure.attachment_type.TEXT)
        
        with allure.step(f"Execute target query for {test_id}"):
            target_results = self._execute_query_with_variables(
                self.db_client, target_query, source_variables
            )
            allure.attach(str(target_results[:10]), name='Target Query Results', 
                         attachment_type=allure.attachment_type.TEXT)
        
        with allure.step(f"Execute validation: {validation_type}"):
            result = self._run_validation(validation_type, source_results, target_results)
            return result
    
    def _run_validation(self, validation_type: str, source_data: Any, target_data: Any) -> Dict[str, Any]:
        """Run specific validation type"""
        
        try:
            if validation_type == 'row_count_comparison':
                source_count = len(source_data)
                target_count = len(target_data)
                
                if source_count == target_count:
                    return {
                        'status': 'PASSED',
                        'source_count': source_count,
                        'target_count': target_count,
                        'message': f'Row counts match: {source_count}'
                    }
                else:
                    return {
                        'status': 'FAILED',
                        'source_count': source_count,
                        'target_count': target_count,
                        'message': f'Count mismatch: Source={source_count}, Target={target_count}'
                    }
            
            elif validation_type == 'duplicate_checks_primary_keys':
                source_ids = set(row[0] for row in source_data)
                target_ids = set(row[0] for row in target_data)
                missing_ids = source_ids - target_ids
                
                if missing_ids:
                    return {
                        'status': 'FAILED',
                        'missing_count': len(missing_ids),
                        'missing_ids': list(missing_ids),
                        'message': f'{len(missing_ids)} IDs missing in target'
                    }
                
                return {
                    'status': 'PASSED',
                    'matched_count': len(source_ids),
                    'message': f'All {len(source_ids)} IDs found in target'
                }
            
            else:
                return {
                    'status': 'SKIPPED',
                    'message': f'Validation type {validation_type} not implemented in demo'
                }
        
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Validation error: {str(e)}'
            }
    
    @pytest.mark.demo
    def test_csv_driven_demo(self):
        """Execute CSV-driven validation demo"""
        
        for test_case in self.test_cases:
            test_id = test_case['test_id']
            test_name = test_case['test_name']
            
            with allure.step(f"Test: {test_id} - {test_name}"):
                result = self._execute_validation(test_case)
                
                if result['status'] == 'SKIPPED':
                    print(f"SKIP {test_id}: {result.get('message')}")
                    continue
                
                assert result['status'] == 'PASSED', result.get('message', 'Validation failed')
                print(f"PASS {test_id}: {result.get('message')}")