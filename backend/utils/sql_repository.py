import os
import re

class SQLRepository:
    def __init__(self, sql_dir="sql"):
        self.sql_dir = sql_dir
        self.queries = {}
        self._load_queries()
    
    def _load_queries(self):
        """Load all SQL queries from files"""
        sql_file = os.path.join(self.sql_dir, "test_queries.sql")
        if os.path.exists(sql_file):
            with open(sql_file, 'r') as f:
                content = f.read()
                self._parse_queries(content)
    
    def _parse_queries(self, content):
        """Parse SQL file and extract queries by ID"""
        # Split by empty lines to get individual queries
        queries = [q.strip() for q in content.split(';') if q.strip()]
        
        for i, query in enumerate(queries, 1):
            if query:
                self.queries[str(i)] = query + ';'
    
    def get_query(self, sql_id):
        """Get SQL query by ID"""
        return self.queries.get(str(sql_id), "")
    
    def list_queries(self):
        """List all available query IDs"""
        return list(self.queries.keys())