export const IS_MOCK = process.env.NEXT_PUBLIC_DATA_MODE === 'mock';
const API_BASE_URL = 'http://localhost:8000/api/v1';

export async function fetchClient(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, defaultOptions);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Utility to delay mock responses
export const mockDelay = (ms: number = 300) => new Promise(resolve => setTimeout(resolve, ms));
