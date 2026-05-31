import React, { createContext, useContext, useState } from 'react';
import { api } from '../services/api';

const AppContext = createContext();

export function AppProvider({ children }) {
  const [activePage, setActivePage] = useState('dashboard');
  const [navParams, setNavParams] = useState({});
  const [activeModule, setActiveModule] = useState('fabric_audit');
  const [featureState, setFeatureState] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [customAlert, setCustomAlert] = useState(null);

  const showAlert = (title, message, type = 'info', onConfirm = null) => {
    setCustomAlert({ title, message, type, onConfirm });
  };

  // Fabric Audit Shared State
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState('bronze_silver');
  const [selectedReport, setSelectedReport] = useState('none');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [reportData, setReportData] = useState(null);

  // Editable Grid State
  const [gridColumns, setGridColumns] = useState([]);
  const [gridData, setGridData] = useState([]);
  const [gridSourceFile, setGridSourceFile] = useState('');

  React.useEffect(() => {
    setIsComplete(false);
    setReportData(null);
    setLogs([]);

    if (selectedReport === 'allure') {
      setGridColumns(['Test_Case', 'Status', 'Duration_ms', 'Error_Message', 'Module']);
      setGridData(Array.from({ length: 20 }, (_, i) => [
        `TC_${1001 + i}`, i % 5 === 0 ? 'Failed' : 'Passed', Math.floor(Math.random() * 500) + 50,
        i % 5 === 0 ? 'Assertion Error: Expected 200 got 500' : 'None', 'Auth_Module'
      ]));
      setGridSourceFile('');
      return;
    }

    if (selectedReport === 'custom') {
      setGridColumns(['Metric_ID', 'Value', 'Threshold', 'Status', 'Timestamp']);
      setGridData(Array.from({ length: 20 }, (_, i) => [
        `MTRC_${800 + i}`, (Math.random() * 100).toFixed(2), '90.00', i % 4 === 0 ? 'Warning' : 'OK', new Date().toISOString().split('T')[0]
      ]));
      setGridSourceFile('');
      return;
    }

    if (selectedDataset !== 'bronze_silver' && selectedDataset !== 'silver_gold') {
      setGridColumns(['Column_A', 'Column_B', 'Column_C', 'Column_D', 'Column_E']);
      setGridData([]);
      setGridSourceFile('');
      return;
    }

    api.getDatasetPreview(selectedDataset)
      .then((data) => {
        setGridColumns(data.columns || []);
        setGridData(data.rows || []);
        setGridSourceFile(data.source_file || '');
      })
      .catch((error) => {
        console.error('Failed to load dataset preview:', error);
        setGridColumns([]);
        setGridData([]);
        setGridSourceFile('');
      });
  }, [selectedDataset, selectedReport]);

  const updateGridCell = (rowIndex, colIndex, value) => {
    setGridData(prev => {
      const newData = [...prev];
      newData[rowIndex] = [...newData[rowIndex]];
      newData[rowIndex][colIndex] = value;
      return newData;
    });
  };

  const addGridRow = () => {
    setGridData(prev => [...prev, new Array(gridColumns.length).fill('')]);
  };

  const deleteGridRow = (rowIndex) => {
    setGridData(prev => prev.filter((_, i) => i !== rowIndex));
  };

  const addGridColumn = (colName = `New_Column`) => {
    setGridColumns(prev => [...prev, colName]);
    setGridData(prev => prev.map(row => [...row, '']));
  };

  const deleteGridColumn = (colIndex) => {
    setGridColumns(prev => prev.filter((_, i) => i !== colIndex));
    setGridData(prev => prev.map(row => row.filter((_, i) => i !== colIndex)));
  };

  // --- LOGIC: LIVE LOG STREAM ---
  React.useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        const timestamp = new Date().toLocaleTimeString();
        const newLogs = [
          `[${timestamp}] SCANNING partition_id=delta_${Math.floor(Math.random() * 1000)}`,
          `[${timestamp}] COMPARING record_offsets ${Math.floor(Math.random() * 5000)}..${Math.floor(Math.random() * 10000)}`,
          `[${timestamp}] STATUS: Processing batch through Neural Bridge...`
        ];
        setLogs(prev => [...prev.slice(-20), ...newLogs]);
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const toggleExecution = async (customQuery = null) => {
    if (isRunning) {
      setIsRunning(false);
      return;
    }

    setIsRunning(true);
    setIsComplete(false);
    setLogs([
      "[SYSTEM] Initializing Fabric Audit Engine...",
      `[INFO] Target Dataset: ${selectedDataset.toUpperCase()}`,
      uploadedFile ? `[INFO] Source: ${uploadedFile.name}` : "[INFO] Source: Default Lakehouse Catalog",
      customQuery ? `[INFO] Using Custom SQL Logic: ${customQuery.slice(0, 50)}...` : "[INFO] Using Default Reconciliation Logic",
      "[PROCESS] Loading reconciliation logic...",
      "[INFO] Validating schema consistency...",
      "[PROCESS] Execution started. Scanning for delta logs..."
    ]);

    try {
      const data = await api.executeAudit(selectedDataset, customQuery);
      // We still use a small timeout to let the logs "feel" real, 
      // but the data now comes from the backend.
      setTimeout(() => {
        setIsRunning(false);
        setIsComplete(true);
        setReportData(data);
      }, 2000);
    } catch (error) {
      console.error("Execution failed:", error);
      setLogs(prev => [...prev, `[ERROR] Execution failed: ${error.message}`]);
      setIsRunning(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadedFile(file);
      setSelectedDataset(file.name); // Automatically select the uploaded file
      setLogs(prev => [`[INFO] File recognized: ${file.name}`, ...prev]);
    }
  };

  // Helper function to easily navigate with parameters
  const navigate = (page, params = {}) => {
    setActivePage(page);
    setNavParams(params);
  };

  const value = {
    activePage, setActivePage,
    navParams, setNavParams,
    activeModule, setActiveModule,
    featureState, setFeatureState,
    isSettingsOpen, setIsSettingsOpen,
    customAlert, setCustomAlert, showAlert,
    isRunning, setIsRunning,
    logs, setLogs,
    showLogs, setShowLogs,
    selectedDataset, setSelectedDataset,
    selectedReport, setSelectedReport,
    uploadedFile, setUploadedFile,
    isComplete, setIsComplete,
    reportData, setReportData,
    gridColumns, gridData, gridSourceFile,
    updateGridCell, addGridRow, deleteGridRow,
    addGridColumn, deleteGridColumn,
    toggleExecution, handleFileUpload,
    navigate
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}
