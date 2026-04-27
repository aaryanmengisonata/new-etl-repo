# 📊 EXCEL USAGE GUIDE - Cross Testing Control

## 🎯 How Business Users Control Testing via Excel

### **Step 1: Open Excel File**
1. Open `Excel_Test_Cases.csv` in Microsoft Excel
2. You'll see columns: functionality, test_id, sql_id, expected_condition, enabled, description, etc.

### **Step 2: Manage Tests in Excel**

#### **Add New Test:**
```
Row 6: etl,ETL_03,15,GREATER_THAN,TRUE,New ETL validation,ETL,MEDIUM,Alex,2024-01-16
```

#### **Disable Test:**
```
Change: enabled = FALSE (for any test you want to skip)
```

#### **Change Priority:**
```
Change: priority = CRITICAL (for urgent tests)
```

### **Step 3: Save Excel as CSV**
1. File → Save As
2. Choose "CSV (Comma delimited)" format
3. Save as `test_cases.csv` in framework folder

### **Step 4: Run Tests from Excel Data**
```bash
# Run all tests from Excel
python etl_runner.py

# Run specific functionality from Excel
python etl_runner.py --functionality database

# Run cross-testing from Excel
python cross_testing_runner.py --demo
```

## 📋 Excel Columns Explained

| **Column** | **Business User Control** | **Example** |
|------------|---------------------------|-------------|
| **functionality** | Business area to test | database, api, etl, integration |
| **test_id** | Unique identifier | DB_01, API_01, ETL_01 |
| **enabled** | Turn test ON/OFF | TRUE = Run, FALSE = Skip |
| **priority** | Test importance | HIGH, MEDIUM, LOW, CRITICAL |
| **owner** | Who manages this test | John, Sarah, Mike |
| **description** | What test does | "Product count validation" |

## 🎯 Cross-Testing Examples in Excel

### **Database + API Cross-Testing:**
```csv
functionality,test_id,description,enabled
cross_validation,CROSS_DB_API,Compare DB count with API count,TRUE
```

### **ETL + Integration Cross-Testing:**
```csv
functionality,test_id,description,enabled
cross_validation,CROSS_ETL_INT,Validate ETL output in integration,TRUE
```

### **Performance Cross-Testing:**
```csv
functionality,test_id,description,enabled
performance,PERF_CROSS,API response time vs DB query time,TRUE
```

## 🚀 Business User Benefits

### **✅ What Business Users Can Do:**
1. **Add new tests** without coding
2. **Enable/disable tests** for different environments
3. **Set priorities** for test execution
4. **Track ownership** of test cases
5. **Control cross-testing** scenarios
6. **Manage test descriptions** for clarity

### **✅ Cross-Testing Control:**
- **API + Database:** Validate data consistency
- **ETL + Integration:** End-to-end pipeline validation
- **Performance + Quality:** Cross-functional testing
- **All Areas Combined:** Comprehensive validation

## 📊 Excel Workflow Summary

```
Excel File → Save as CSV → Run Framework → Get Results
     ↑                                           ↓
Business Control                            XML + Allure Reports
```

**Result: Business users control ALL testing areas from Excel! 🎯**