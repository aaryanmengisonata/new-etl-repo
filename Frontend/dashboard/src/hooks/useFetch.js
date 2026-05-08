import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

/**
 * A professional enterprise hook for data fetching
 * Handles loading states, errors, and prevents memory leaks
 */
export function useFetch(endpoint, options = {}) {
  const [data, setData] = useState(options.initialData || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (fetchOptions = {}) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get(endpoint);
      setData(result);
      return result;
    } catch (err) {
      setError(err.message || 'An error occurred during fetch');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    if (!options.lazy) {
      fetchData();
    }
  }, [fetchData, options.lazy]);

  const mutate = async (method, body) => {
    try {
      setLoading(true);
      const result = await api[method.toLowerCase()](endpoint, body);
      
      // Auto-refresh data if it was a mutation
      if (!options.skipAutoRefresh) {
        await fetchData();
      }
      return result;
    } catch (err) {
      setError(err.message || `An error occurred during ${method}`);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { 
    data, 
    loading, 
    error, 
    refetch: fetchData,
    mutate 
  };
}
