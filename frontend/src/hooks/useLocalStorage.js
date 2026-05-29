import { useState, useEffect } from 'react'

/**
 * Custom hook for localStorage with auto-sync
 * @param {string} key - localStorage key
 * @param {any} initialValue - Default value if key doesn't exist
 * @returns {[any, Function]} Current value and setter function
 */
export function useLocalStorage(key, initialValue) {
  // Initialize state with value from localStorage or default
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? JSON.parse(item) : initialValue
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error)
      return initialValue
    }
  })

  // Update localStorage when state changes
  const setValue = (value) => {
    try {
      // Allow value to be a function for same API as useState
      const valueToStore = value instanceof Function ? value(storedValue) : value
      
      setStoredValue(valueToStore)
      window.localStorage.setItem(key, JSON.stringify(valueToStore))
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error)
    }
  }

  return [storedValue, setValue]
}

/**
 * Hook for managing nested localStorage object
 * @param {string} key - localStorage key
 * @param {object} initialValue - Default object structure
 * @returns {[any, Function, Function]} Value, setter, and field updater
 */
export function useLocalStorageObject(key, initialValue = {}) {
  const [value, setValue] = useLocalStorage(key, initialValue)

  // Update a specific field in the object
  const updateField = (field, newValue) => {
    setValue(prev => ({
      ...prev,
      [field]: newValue
    }))
  }

  return [value, setValue, updateField]
}
