// @ts-nocheck
// src/hooks/useApi.ts
// Hook לשימוש ב-API עם טיפול בשגיאות וטעינה

import { useState, useCallback } from 'react';
import api from '../services/api';

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

export const useApi = <T = any>(options?: UseApiOptions) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<any>(null);

  const execute = useCallback(async (
    apiCall: () => Promise<any>,
    callOptions?: UseApiOptions
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiCall();
      setData(response);
      
      if (callOptions?.onSuccess || options?.onSuccess) {
        (callOptions?.onSuccess || options?.onSuccess)?.(response);
      }
      
      return response;
    } catch (err: any) {
      setError(err);
      
      if (callOptions?.onError || options?.onError) {
        (callOptions?.onError || options?.onError)?.(err);
      } else {
        console.error('API Error:', err);
      }
      
      throw err;
    } finally {
      setLoading(false);
    }
  }, [options]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset
  };
};

export default useApi;













