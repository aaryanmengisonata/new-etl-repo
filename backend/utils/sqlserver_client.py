"""SQL Server Client for AX Database"""
import pyodbc
import configparser


class SQLServerClient:
    def __init__(self, config_section='AX_SOURCE'):
        self.config = configparser.ConfigParser()
        self.config.read('config/master.properties')
        self.section = config_section
        self.connection = None
        
    def connect(self):
        """Connect to SQL Server"""
        # Try both naming conventions: SECTION_KEY and KEY
        def get_config(key, fallback=None):
            prefix = self.section.split('_')[0]
            try:
                return self.config.get(self.section, f'{prefix}_{key}')
            except:
                try:
                    return self.config.get(self.section, key)
                except:
                    if fallback is not None:
                        return fallback
                    raise
        
        server = get_config('SERVER')
        port = get_config('PORT', '1433')
        database = get_config('DATABASE')
        auth_method = get_config('AUTH_METHOD', 'Windows')
        
        if auth_method == 'Windows':
            conn_str = (
                f"Driver={{ODBC Driver 18 for SQL Server}};"
                f"Server={server},{port};"
                f"Database={database};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
        else:
            username = get_config('USERNAME')
            password = get_config('PASSWORD')
            conn_str = (
                f"Driver={{ODBC Driver 18 for SQL Server}};"
                f"Server={server},{port};"
                f"Database={database};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate=yes;"
            )
        
        self.connection = pyodbc.connect(conn_str)
        return self.connection
    
    def execute_query(self, query):
        """Execute SQL query and return results"""
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    
    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
