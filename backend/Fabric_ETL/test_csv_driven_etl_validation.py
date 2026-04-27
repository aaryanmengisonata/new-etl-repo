import pytest
import allure
import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Any
try:
    from utils.fabric_client import FabricClient
    from utils.predefined_validations import PredefinedValidations
except ImportError:
    from fabric_client import FabricClient
    from predefined_validations import PredefinedValidations

@allure.epic("ETL Testing Framework")
@allure.feature("CSV-Driven ETL Validation")
class TestCSVDrivenETLValidation:
    """CSV-Driven ETL Validation - Manual testers control tests via CSV"""
    
    @classmethod
    def setup_class(cls):
        """Setup database clients and load CSV tests"""
        cls.source_client = FabricClient('BRONZE')
        cls.target_client = FabricClient('SILVER')
        cls.validator = PredefinedValidations()
        cls.test_cases = cls._load_test_cases()
    
    @classmethod
    def _load_test_cases(cls) -> List[Dict]:
        """Load test cases from CSV"""
        csv_file = cls._resolve_csv_path()
        df = pd.read_csv(csv_file)
        df = df.fillna('')
        df['enabled'] = df['enabled'].astype(str)
        enabled_df = df[df['enabled'].str.upper() == 'TRUE']
        return enabled_df.to_dict('records')

    @staticmethod
    def _resolve_csv_path() -> str:
        candidates = [
            Path('etl_validation_tests.csv'),
            Path('data') / 'etl_validation_tests.csv',
            Path(__file__).resolve().parent / 'etl_validation_tests.csv',
            Path(__file__).resolve().parent / 'data' / 'etl_validation_tests.csv',
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        raise FileNotFoundError(
            'etl_validation_tests.csv not found. Place it in project root or data/.'
        )
    
    @staticmethod
    def _resolve_query_variables(query: str, variables: Dict[str, Any]) -> str:
        """Resolve {var} placeholders in query text."""
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in query:
                if isinstance(var_value, list):
                    var_value = ','.join(map(str, var_value))
                query = query.replace(placeholder, str(var_value))
        return query

    @staticmethod
    def _execute_query_with_variables(client, query: str, variables: Dict[str, Any]) -> Any:
        """Execute query with variable substitution"""
        query = TestCSVDrivenETLValidation._resolve_query_variables(query, variables)
        return client.execute_query(query)
    
    @staticmethod
    def _extract_variables_from_query(query: str) -> List[str]:
        """Extract variable names from query"""
        return re.findall(r'\{(\w+)\}', query)

    @staticmethod
    def _derive_table_name(test_case: Dict) -> str:
        """Derive table name from CSV or source query when not explicitly provided."""
        explicit_table = str(test_case.get('table_name', '')).strip()
        if explicit_table and explicit_table.upper() != 'N/A':
            if ',' in explicit_table:
                return 'MULTI_TABLE'
            return explicit_table

        source_query = str(test_case.get('source_query', ''))
        if 'WITH Combined AS' in source_query.upper():
            return 'MULTI_TABLE'

        match = re.search(r'FROM\s+([A-Za-z0-9_\.\[\]]+)', source_query, flags=re.IGNORECASE)
        if match:
            return match.group(1)
        return 'N/A'

    @classmethod
    def _derive_lakehouse_names(cls, test_case: Dict) -> Dict[str, str]:
        """Derive source/target lakehouse names from CSV or query text."""
        source_lakehouse = cls._csv_value(test_case, 'source_lakehouse')
        target_lakehouse = cls._csv_value(test_case, 'target_lakehouse')

        source_query = str(test_case.get('source_query', ''))
        target_query = str(test_case.get('target_query', ''))

        if not source_lakehouse:
            source_match = re.search(
                r'FROM\s+([A-Za-z0-9_\[\]]+)\.[A-Za-z0-9_\[\]]+\.[A-Za-z0-9_\[\]]+',
                source_query,
                flags=re.IGNORECASE
            )
            source_lakehouse = source_match.group(1) if source_match else 'N/A'

        if not target_lakehouse:
            target_match = re.search(
                r'FROM\s+([A-Za-z0-9_\[\]]+)\.[A-Za-z0-9_\[\]]+\.[A-Za-z0-9_\[\]]+',
                target_query,
                flags=re.IGNORECASE
            )
            target_lakehouse = target_match.group(1) if target_match else 'N/A'

        return {'source_lakehouse': source_lakehouse, 'target_lakehouse': target_lakehouse}

    @staticmethod
    def _csv_value(test_case: Dict, key: str, default: str = '') -> str:
        """Read CSV field as a trimmed string with default fallback."""
        value = str(test_case.get(key, default)).strip()
        return value if value and value.upper() != 'N/A' else default

    @classmethod
    def _csv_list(cls, test_case: Dict, key: str, default: List[str]) -> List[str]:
        """Read comma-separated CSV field into list."""
        raw = cls._csv_value(test_case, key, '')
        if not raw:
            return list(default)
        return [item.strip() for item in raw.split(',') if item.strip()]

    @classmethod
    def _csv_float(cls, test_case: Dict, key: str, default: float = 0.0) -> float:
        """Read numeric CSV field with fallback."""
        raw = cls._csv_value(test_case, key, '')
        if not raw:
            return float(default)
        return float(raw)

    @classmethod
    def _build_dynamic_queries(cls, test_case: Dict) -> Dict[str, str]:
        """Build source/target queries dynamically from CSV metadata when needed.

        Expected optional CSV columns:
        - source_lakehouse, target_lakehouse
        - table_name (single table or comma-separated list)
        - source_schema (default: fullload), target_schema (default: dbo)
        - target_lhname_column (default: lhname)
        - target_lhname_value (default: source_lakehouse)
        - source_where, target_where
        """
        source_query = cls._csv_value(test_case, 'source_query')
        target_query = cls._csv_value(test_case, 'target_query')
        if source_query and target_query:
            return {'source_query': source_query, 'target_query': target_query}

        source_lakehouse = cls._csv_value(test_case, 'source_lakehouse')
        target_lakehouse = cls._csv_value(test_case, 'target_lakehouse')
        tables_raw = cls._csv_value(test_case, 'table_name')

        if not (source_lakehouse and target_lakehouse and tables_raw):
            raise ValueError(
                "Missing query configuration. Provide source_query/target_query or "
                "source_lakehouse, target_lakehouse, and table_name."
            )

        source_schema = cls._csv_value(test_case, 'source_schema', 'fullload')
        target_schema = cls._csv_value(test_case, 'target_schema', 'dbo')
        target_lhname_column = cls._csv_value(test_case, 'target_lhname_column', 'lhname')
        target_lhname_value = cls._csv_value(test_case, 'target_lhname_value', source_lakehouse)
        source_where = cls._csv_value(test_case, 'source_where')
        target_where = cls._csv_value(test_case, 'target_where')

        tables = [table.strip() for table in tables_raw.split(',') if table.strip()]
        if not tables:
            raise ValueError("table_name must contain at least one table.")

        source_where_clause = f" WHERE {source_where}" if source_where else ""
        target_conditions = [f"{target_lhname_column}='{target_lhname_value}'"]
        if target_where:
            target_conditions.append(target_where)
        target_where_clause = " WHERE " + " AND ".join(target_conditions)

        if len(tables) == 1:
            table = tables[0]
            source_query = (
                f"SELECT COUNT(*) AS row_count FROM {source_lakehouse}.{source_schema}.{table}"
                f"{source_where_clause}"
            )
            target_query = (
                f"SELECT COUNT(*) AS row_count FROM {target_lakehouse}.{target_schema}.{table}"
                f"{target_where_clause}"
            )
            return {'source_query': source_query, 'target_query': target_query}

        source_parts = []
        target_parts = []
        for table in tables:
            source_parts.append(
                f"(SELECT COUNT(*) FROM {source_lakehouse}.{source_schema}.{table}{source_where_clause}) AS {table}"
            )
            target_parts.append(
                f"(SELECT COUNT(*) FROM {target_lakehouse}.{target_schema}.{table}{target_where_clause}) AS {table}"
            )

        source_query = "SELECT " + ", ".join(source_parts)
        target_query = "SELECT " + ", ".join(target_parts)
        return {'source_query': source_query, 'target_query': target_query}

    @classmethod
    def _build_query_variables(cls, test_case: Dict) -> Dict[str, Any]:
        """Build placeholder variables from CSV fields for query templates."""
        variables: Dict[str, Any] = {}
        for key, value in test_case.items():
            if isinstance(value, str):
                variables[key] = value.strip()
            else:
                variables[key] = value
        return variables

    @classmethod
    def _get_table_list(cls, test_case: Dict) -> List[str]:
        """Return table names from CSV field (supports comma-separated values)."""
        raw_tables = cls._csv_value(test_case, 'table_name')
        if not raw_tables:
            return []
        return [table.strip() for table in raw_tables.split(',') if table.strip()]
    
    def _execute_validation(self, test_case: Dict) -> Dict[str, Any]:
        """Execute validation based on test case configuration"""
        
        test_id = test_case['test_id']
        query_config = self._build_dynamic_queries(test_case)
        query_variables = self._build_query_variables(test_case)
        validation_type = test_case['validation_type']
        table_list = self._get_table_list(test_case)

        template_uses_table_placeholder = (
            '{table_name}' in query_config['source_query'] or '{table_name}' in query_config['target_query']
        )

        # If query templates use {table_name} and CSV provides multiple tables,
        # execute each table independently with same setup and aggregate outcome.
        if template_uses_table_placeholder and len(table_list) > 1:
            per_table_results = []

            for table_name in table_list:
                with allure.step(f"Execute table {table_name} for {test_id}"):
                    table_vars = dict(query_variables)
                    table_vars['table_name'] = table_name
                    source_query = self._resolve_query_variables(query_config['source_query'], table_vars)
                    target_query = self._resolve_query_variables(query_config['target_query'], table_vars)
                    try:
                        with allure.step(f"Execute source query for {test_id} - {table_name}"):
                            source_variables = {}
                            target_vars = self._extract_variables_from_query(target_query)

                            source_results = self.source_client.execute_query(source_query)
                            allure.attach(
                                str(source_results[:10]),
                                name=f'Source Query Results (sample) - {table_name}',
                                attachment_type=allure.attachment_type.TEXT
                            )

                            if 'recid_list' in target_vars:
                                recid_list = [row['recid'] for row in source_results]
                                source_variables['recid_list'] = recid_list
                                allure.attach(
                                    str(recid_list[:20]),
                                    name=f'RecID List (first 20) - {table_name}',
                                    attachment_type=allure.attachment_type.TEXT
                                )

                        with allure.step(f"Execute target query for {test_id} - {table_name}"):
                            target_results = self._execute_query_with_variables(
                                self.target_client, target_query, source_variables
                            )
                            allure.attach(
                                str(target_results[:10]),
                                name=f'Target Query Results (sample) - {table_name}',
                                attachment_type=allure.attachment_type.TEXT
                            )

                        with allure.step(f"Execute validation: {validation_type} - {table_name}"):
                            runtime_test_case = dict(test_case)
                            runtime_test_case['table_name'] = table_name
                            runtime_test_case['source_query'] = source_query
                            runtime_test_case['target_query'] = target_query
                            result = self._run_validation(
                                validation_type, source_results, target_results, runtime_test_case
                            )
                            per_table_results.append({'table_name': table_name, 'result': result})
                    except Exception as exc:
                        per_table_results.append({
                            'table_name': table_name,
                            'result': {
                                'status': 'ERROR',
                                'source_count': 0,
                                'target_count': 0,
                                'message': (
                                    f"Query execution failed for table {table_name}: {exc}. "
                                    f"Source query: {source_query} | Target query: {target_query}"
                                )
                            }
                        })

            failed_tables = [
                item for item in per_table_results if item['result'].get('status') != 'PASSED'
            ]

            if failed_tables:
                first_failure = failed_tables[0]
                return {
                    'status': first_failure['result'].get('status', 'FAILED'),
                    'source_count': sum(
                        int(item['result'].get('source_count', 0)) for item in per_table_results
                    ),
                    'target_count': sum(
                        int(item['result'].get('target_count', 0)) for item in per_table_results
                    ),
                    'message': (
                        f"Validation failed for {len(failed_tables)} table(s). "
                        f"First failure [{first_failure['table_name']}]: "
                        f"{first_failure['result'].get('message', 'Validation failed')}"
                    )
                }

            return {
                'status': 'PASSED',
                'source_count': sum(
                    int(item['result'].get('source_count', 0)) for item in per_table_results
                ),
                'target_count': sum(
                    int(item['result'].get('target_count', 0)) for item in per_table_results
                ),
                'matched_count': len(per_table_results),
                'message': f"All {len(per_table_results)} table validations passed"
            }

        source_query = self._resolve_query_variables(query_config['source_query'], query_variables)
        target_query = self._resolve_query_variables(query_config['target_query'], query_variables)
        
        with allure.step(f"Execute source query for {test_id}"):
            source_variables = {}
            target_vars = self._extract_variables_from_query(target_query)
            
            source_results = self.source_client.execute_query(source_query)
            allure.attach(str(source_results[:10]), name='Source Query Results (sample)', 
                         attachment_type=allure.attachment_type.TEXT)
            
            if 'recid_list' in target_vars:
                recid_list = [row['recid'] for row in source_results]
                source_variables['recid_list'] = recid_list
                allure.attach(str(recid_list[:20]), name='RecID List (first 20)', 
                             attachment_type=allure.attachment_type.TEXT)
        
        with allure.step(f"Execute target query for {test_id}"):
            target_results = self._execute_query_with_variables(
                self.target_client, target_query, source_variables
            )
            allure.attach(str(target_results[:10]), name='Target Query Results (sample)', 
                         attachment_type=allure.attachment_type.TEXT)
        
        with allure.step(f"Execute validation: {validation_type}"):
            runtime_test_case = dict(test_case)
            runtime_test_case['source_query'] = source_query
            runtime_test_case['target_query'] = target_query
            result = self._run_validation(
                validation_type, source_results, target_results, runtime_test_case
            )
            return result
    
    def _run_validation(self, validation_type: str, source_data: Any, 
                       target_data: Any, test_case: Dict) -> Dict[str, Any]:
        """Run specific validation type"""
        
        try:
            normalized_validation = str(validation_type).strip().lower()

            if normalized_validation == 'row_count_comparison':
                source_count, target_count = self.validator.row_count_comparison(
                    source_data, target_data
                )
                return {
                    'status': 'PASSED',
                    'source_count': source_count,
                    'target_count': target_count,
                    'message': f'Row counts match: {source_count}'
                }
            
            elif normalized_validation in ('insert_record_validation', 'update_record_validation', 'delete_record_validation'):
                source_recids = set(row['recid'] for row in source_data)
                target_recids = set(row['recid'] for row in target_data)
                missing_recids = source_recids - target_recids
                
                if missing_recids:
                    return {
                        'status': 'FAILED',
                        'source_count': len(source_recids),
                        'target_count': len(target_recids),
                        'missing_count': len(missing_recids),
                        'missing_recids': list(missing_recids)[:10],
                        'message': f'{len(missing_recids)} recids missing in target'
                    }
                
                return {
                    'status': 'PASSED',
                    'source_count': len(source_recids),
                    'target_count': len(source_recids),
                    'matched_count': len(source_recids),
                    'message': f'All {len(source_recids)} recids found in target'
                }
            
            elif normalized_validation == 'soft_delete_consistency':
                key_columns = self._csv_list(test_case, 'key_columns', ['recid'])
                delete_column = self._csv_value(test_case, 'delete_column', 'isdelete')
                summary = self.validator.soft_delete_consistency(
                    source_data=source_data,
                    target_data=target_data,
                    key_columns=key_columns,
                    delete_column=delete_column
                )
                return {
                    'status': 'PASSED',
                    'source_count': len(source_data),
                    'target_count': len(target_data),
                    'matched_count': summary['joined_row_count'],
                    'message': f"Soft delete consistency passed for {summary['joined_row_count']} joined records"
                }

            elif normalized_validation in ('record_level_dataframe_comparison', 'record_level_comparison', 'insert_record_validation_group', 'update_record_validation_group', 'delete_record_validation_group'):
                key_columns = self._csv_list(test_case, 'key_columns', ['recid'])
                if source_data and target_data:
                    source_cols = set(source_data[0].keys()) if hasattr(source_data[0], 'keys') else set()
                    target_cols = set(target_data[0].keys()) if hasattr(target_data[0], 'keys') else set()
                    if 'TableName' in source_cols and 'TableName' in target_cols and key_columns == ['recid']:
                        key_columns = ['TableName', 'recid']

                target_query = str(test_case.get('target_query', ''))
                if '{recid_list}' in target_query:
                    source_df = self.validator._to_dataframe(source_data, dataset_name='source_data')
                    target_df = self.validator._to_dataframe(target_data, dataset_name='target_data')

                    source_keys = set(map(tuple, source_df[key_columns].drop_duplicates().to_records(index=False)))
                    target_keys = set(map(tuple, target_df[key_columns].drop_duplicates().to_records(index=False)))

                    missing_keys = source_keys - target_keys
                    if missing_keys:
                        return {
                            'status': 'FAILED',
                            'source_count': len(source_keys),
                            'target_count': len(target_keys),
                            'missing_count': len(missing_keys),
                            'message': f'{len(missing_keys)} source keys missing in target. Sample: {list(missing_keys)[:10]}'
                        }

                    return {
                        'status': 'PASSED',
                        'source_count': len(source_keys),
                        'target_count': len(target_keys),
                        'matched_count': len(source_keys),
                        'message': f'All {len(source_keys)} source keys found in target'
                    }

                compare_columns = self._csv_list(test_case, 'compare_columns', [])
                compare_cols_arg = compare_columns if compare_columns else None

                summary = self.validator.record_level_dataframe_comparison(
                    source_data=source_data,
                    target_data=target_data,
                    key_columns=key_columns,
                    compare_columns=compare_cols_arg
                )
                return {
                    'status': 'PASSED',
                    'source_count': len(source_data),
                    'target_count': len(target_data),
                    'matched_count': len(source_data) - summary['missing_in_target_count'],
                    'message': f"Record-level comparison passed for keys {key_columns}"
                }

            elif normalized_validation in ('incremental_validation', 'incremental_delta_validation'):
                watermark_column = self._csv_value(test_case, 'watermark_column', 'dpmodifieddatetime')
                key_columns = self._csv_list(test_case, 'key_columns', ['recid'])
                delta_start = self._csv_value(test_case, 'delta_start', '')
                delta_end = self._csv_value(test_case, 'delta_end', '')
                summary = self.validator.incremental_delta_validation(
                    source_data=source_data,
                    target_data=target_data,
                    watermark_column=watermark_column,
                    key_columns=key_columns,
                    delta_start=delta_start or None,
                    delta_end=delta_end or None,
                    allow_empty_delta=True
                )
                return {
                    'status': 'PASSED',
                    'source_count': summary['source_delta_rows'],
                    'target_count': summary['target_delta_rows'],
                    'matched_count': summary['source_delta_rows'] - summary['missing_key_count'],
                    'message': f"Incremental validation passed for range {summary['delta_start']} to {summary['delta_end']}"
                }

            elif normalized_validation in ('duplicate_check', 'duplicate_checks', 'duplicate_checks_primary_keys'):
                key_columns = self._csv_list(test_case, 'key_columns', ['recid'])
                source_dups = self.validator.duplicate_checks_primary_keys(source_data, key_columns)
                target_dups = self.validator.duplicate_checks_primary_keys(target_data, key_columns)
                return {
                    'status': 'PASSED',
                    'source_count': len(source_data),
                    'target_count': len(target_data),
                    'matched_count': len(source_data),
                    'message': (
                        f"Duplicate check passed on keys {key_columns}. "
                        f"Source duplicates={source_dups}, Target duplicates={target_dups}"
                    )
                }

            elif normalized_validation in ('aggregate_validation', 'aggregate_validations'):
                aggregate_columns = self._csv_list(test_case, 'aggregate_columns', [])
                aggregate_functions = self._csv_list(test_case, 'aggregate_functions', ['sum'])
                tolerance = self._csv_float(test_case, 'aggregate_tolerance', 0.0)

                if not aggregate_columns:
                    raise AssertionError("aggregate_columns is required for aggregate_validation.")

                aggregate_config = {col: aggregate_functions for col in aggregate_columns}
                self.validator.aggregate_validations(
                    source_data=source_data,
                    target_data=target_data,
                    aggregate_config=aggregate_config,
                    tolerance=tolerance
                )
                return {
                    'status': 'PASSED',
                    'source_count': len(source_data),
                    'target_count': len(target_data),
                    'matched_count': len(source_data),
                    'message': (
                        f"Aggregate validation passed for columns {aggregate_columns} "
                        f"with functions {aggregate_functions}"
                    )
                }

            elif normalized_validation in ('referential_integrity', 'referential_integrity_validation'):
                child_fk_columns = self._csv_list(test_case, 'child_fk_columns', ['recid'])
                parent_pk_columns = self._csv_list(test_case, 'parent_pk_columns', child_fk_columns)
                missing_count = self.validator.referential_integrity_validation(
                    child_data=source_data,
                    parent_data=target_data,
                    child_fk_columns=child_fk_columns,
                    parent_pk_columns=parent_pk_columns
                )
                return {
                    'status': 'PASSED',
                    'source_count': len(source_data),
                    'target_count': len(target_data),
                    'matched_count': len(source_data) - missing_count,
                    'message': f"Referential integrity passed for FK {child_fk_columns} -> PK {parent_pk_columns}"
                }

            elif normalized_validation == "null_checks_mandatory_columns":
                mandatory_columns = self._csv_list(
                    test_case,
                    'mandatory_columns',
                    ["recid", "isdelete", "dpcreateddatetime", "dpmodifieddatetime"]
                )
                result_data = PredefinedValidations.null_checks_mandatory_columns(
                    target_data,
                    mandatory_columns
                )
                return {
                    "status": "PASSED",
                    **result_data,
                    "message": f"Validated {result_data['total_rows_verified']} rows successfully."
                }
            else:
                return {
                    'status': 'FAILED',
                    'message': f'Unknown validation type: {validation_type}'
                }
        
        except AssertionError as e:
            return {
                'status': 'FAILED',
                'message': str(e)
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Validation error: {str(e)}'
            }
    
    def pytest_generate_tests(self, metafunc):
        """Generate tests dynamically from CSV"""
        if 'test_case' in metafunc.fixturenames:
            test_cases = self._load_test_cases()
            metafunc.parametrize('test_case', test_cases, ids=[tc['test_id'] for tc in test_cases])
    
    @pytest.mark.fabric
    @pytest.mark.etl
    def test_csv_driven_validation(self, test_case):
        """Execute CSV-driven ETL validation test"""
        
        test_id = test_case['test_id']
        test_name = test_case['test_name']
        description = test_case['description']
        table_name = self._derive_table_name(test_case)
        lakehouses = self._derive_lakehouse_names(test_case)
        validation_type = test_case['validation_type']
        
        allure.dynamic.title(f"{test_id}: {test_name}")
        allure.dynamic.description(description)
        
        allure.dynamic.label("Table", table_name)
        allure.dynamic.label("Source_Lakehouse", lakehouses['source_lakehouse'])
        allure.dynamic.label("Target_Lakehouse", lakehouses['target_lakehouse'])
        allure.dynamic.label("Validation", validation_type.replace('_', ' ').title())
        
        result = self._execute_validation(test_case)
        
        if 'source_count' in result and 'target_count' in result:
            allure.dynamic.label("Source_Count", str(result['source_count']))
            allure.dynamic.label("Target_Count", str(result['target_count']))
            allure.dynamic.label("Match_Status", f"S:{result['source_count']}=T:{result['target_count']}")
        
        with allure.step("Validation Results"):
            result_summary = f"""Table: {table_name}
Source Lakehouse: {lakehouses['source_lakehouse']}
Target Lakehouse: {lakehouses['target_lakehouse']}
Validation: {validation_type}
Status: {result['status']}
Message: {result.get('message')}"""
            
            if 'source_count' in result:
                result_summary += f"\nSource Count: {result['source_count']}"
            if 'target_count' in result:
                result_summary += f"\nTarget Count: {result['target_count']}"
            if 'matched_count' in result:
                result_summary += f"\nMatched Records: {result['matched_count']}"
            
            allure.attach(result_summary, name='Validation Summary', 
                         attachment_type=allure.attachment_type.TEXT)
        
        assert result['status'] == 'PASSED', result.get('message', 'Validation failed')
        print(f"PASS: {test_id}: {result.get('message', 'PASSED')}")
