from jsonschema import validate, ValidationError
import logging

class DataValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_json_schema(self, data, schema):
        """Validate data against JSON schema"""
        try:
            validate(instance=data, schema=schema)
            return True, None
        except ValidationError as e:
            self.logger.error(f"Schema validation failed: {e.message}")
            return False, e.message
    
    def validate_data_types(self, data, type_mapping):
        """Validate data types according to mapping"""
        errors = []
        for field, expected_type in type_mapping.items():
            if field in data:
                actual_value = data[field]
                if expected_type == 'int' and not isinstance(actual_value, int):
                    errors.append(f"Field '{field}' should be int, got {type(actual_value).__name__}")
                elif expected_type == 'float' and not isinstance(actual_value, (int, float)):
                    errors.append(f"Field '{field}' should be float, got {type(actual_value).__name__}")
                elif expected_type == 'str' and not isinstance(actual_value, str):
                    errors.append(f"Field '{field}' should be string, got {type(actual_value).__name__}")
        
        return len(errors) == 0, errors
    
    def validate_required_fields(self, data, required_fields):
        """Validate that all required fields are present"""
        missing_fields = [field for field in required_fields if field not in data]
        return len(missing_fields) == 0, missing_fields
    
    def validate_data_ranges(self, data, range_rules):
        """Validate data ranges (e.g., price > 0)"""
        errors = []
        for field, rule in range_rules.items():
            if field in data:
                value = data[field]
                if 'min' in rule and value < rule['min']:
                    errors.append(f"Field '{field}' value {value} is below minimum {rule['min']}")
                if 'max' in rule and value > rule['max']:
                    errors.append(f"Field '{field}' value {value} is above maximum {rule['max']}")
        
        return len(errors) == 0, errors