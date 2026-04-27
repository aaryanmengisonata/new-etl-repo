import xml.etree.ElementTree as ET
from datetime import datetime
import os

class XMLReportGenerator:
    def __init__(self, output_dir="reports/xml-results"):
        self.output_dir = output_dir
        self.test_results = []
        os.makedirs(output_dir, exist_ok=True)
    
    def add_test_result(self, test_id, functionality, status, execution_time, error_message=None):
        """Add test result to collection"""
        self.test_results.append({
            'test_id': test_id,
            'functionality': functionality,
            'status': status,
            'execution_time': execution_time,
            'error_message': error_message,
            'timestamp': datetime.now()
        })
    
    def generate_xml_report(self, filename="test_results.xml"):
        """Generate XML report similar to their framework"""
        
        # Create root element
        root = ET.Element("testsuites")
        root.set("name", "ETL Test Results")
        root.set("timestamp", datetime.now().isoformat())
        
        # Group by functionality
        functionalities = {}
        for result in self.test_results:
            func = result['functionality']
            if func not in functionalities:
                functionalities[func] = []
            functionalities[func].append(result)
        
        total_tests = len(self.test_results)
        total_failures = len([r for r in self.test_results if r['status'] == 'FAILED'])
        total_time = sum([r['execution_time'] for r in self.test_results])
        
        root.set("tests", str(total_tests))
        root.set("failures", str(total_failures))
        root.set("time", str(total_time))
        
        # Create testsuite for each functionality
        for func_name, results in functionalities.items():
            testsuite = ET.SubElement(root, "testsuite")
            testsuite.set("name", func_name)
            testsuite.set("tests", str(len(results)))
            testsuite.set("failures", str(len([r for r in results if r['status'] == 'FAILED'])))
            testsuite.set("time", str(sum([r['execution_time'] for r in results])))
            
            # Add test cases
            for result in results:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", result['test_id'])
                testcase.set("classname", func_name)
                testcase.set("time", str(result['execution_time']))
                
                if result['status'] == 'FAILED':
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", result['error_message'] or "Test failed")
                    failure.text = result['error_message'] or "No error details"
        
        # Write XML file
        tree = ET.ElementTree(root)
        output_path = os.path.join(self.output_dir, filename)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        return output_path
    
    def generate_summary_report(self):
        """Generate summary report"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAILED'])
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'execution_time': sum([r['execution_time'] for r in self.test_results])
        }
        
        return summary