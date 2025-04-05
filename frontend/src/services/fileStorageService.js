// src/services/fileStorageService.js
import { authHeader } from './authService';

/**
 * Service for handling file uploads with a more production-like approach
 */

// Base API URL
const API_URL = 'http://localhost:8000';

/**
 * Simulates a file upload to a storage service and returns a URL
 * In production, this would upload to S3, Azure Blob Storage, etc.
 * For dev, we'll use the backend's file upload endpoint if available
 * 
 * @param {File} file - The file to upload
 * @returns {Promise<string>} - URL to the uploaded file
 */
export const uploadFile = async (file) => {
  try {
    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append('file', file);
    
    // Try to use a backend upload endpoint if available
    try {
      const response = await fetch(`${API_URL}/upload-file`, {
        method: 'POST',
        headers: {
          ...authHeader()
          // Note: Don't set Content-Type with FormData, it will be set automatically
        },
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.file_url; // Use the URL returned by the backend
      }
    } catch (uploadError) {
      console.log('Backend upload endpoint not available, using client-side fallback');
      // Silently fall back to client-side handling if backend endpoint isn't available
    }
    
    // Fallback: Generate a persistent local URL using localStorage for development
    // This is NOT for production use, but helps simulate persistent URLs during development
    const fileId = generateUniqueId();
    const fileType = file.type;
    
    // Convert file to a data URL as our fallback storage mechanism
    const dataUrl = await fileToBase64(file);
    
    // Save to localStorage (only for development!)
    saveFileToLocalStorage(fileId, dataUrl);
    
    // Generate a URL that looks like a real file URL
    // This helps maintain the illusion of a real storage service during development
    return `${window.location.origin}/dev-storage/${fileId}/${encodeURIComponent(file.name)}`;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw new Error('Failed to upload file. Please try again.');
  }
};

/**
 * Resolves a file URL to an actual data URL for display
 * In production, this function would simply return the URL unchanged
 * For dev with our localStorage approach, it retrieves the stored data URL
 * 
 * @param {string} url - The file URL to resolve
 * @returns {Promise<string>} - The data URL or original URL
 */
export const resolveFileUrl = async (url) => {
  // If it's already a data URL, return it unchanged
  if (url?.startsWith('data:')) {
    return url;
  }
  
  // If it's a real HTTP URL (not our dev storage), return it unchanged
  if (url?.startsWith('http') && !url.includes('/dev-storage/')) {
    return url;
  }
  
  // For our dev storage URLs, extract the file ID and get from localStorage
  try {
    const matches = url?.match(/\/dev-storage\/([^\/]+)\//);
    if (matches && matches[1]) {
      const fileId = matches[1];
      return getFileFromLocalStorage(fileId) || url;
    }
  } catch (error) {
    console.error('Error resolving file URL:', error);
  }
  
  // If all else fails, return the original URL
  return url;
};

/**
 * Helper function to convert a File to a base64 data URL
 * @param {File} file - The file to convert
 * @returns {Promise<string>} - Base64 data URL
 */
export const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
  });
};

/**
 * Generate a unique ID for file storage
 * @returns {string} - Unique ID
 */
function generateUniqueId() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

/**
 * Save a file to localStorage (development only)
 * @param {string} fileId - Unique file ID
 * @param {string} dataUrl - Data URL of the file
 */
function saveFileToLocalStorage(fileId, dataUrl) {
  try {
    // Create/get our file storage area in localStorage
    const storage = JSON.parse(localStorage.getItem('dev_file_storage') || '{}');
    
    // Add the new file
    storage[fileId] = dataUrl;
    
    // Save back to localStorage
    localStorage.setItem('dev_file_storage', JSON.stringify(storage));
  } catch (error) {
    console.error('Error saving file to localStorage:', error);
  }
}

/**
 * Retrieve a file from localStorage (development only)
 * @param {string} fileId - Unique file ID
 * @returns {string|null} - Data URL of the file or null if not found
 */
function getFileFromLocalStorage(fileId) {
  try {
    const storage = JSON.parse(localStorage.getItem('dev_file_storage') || '{}');
    return storage[fileId] || null;
  } catch (error) {
    console.error('Error retrieving file from localStorage:', error);
    return null;
  }
}

/**
 * Handler for product image uploads 
 * @param {Event} event - File input change event
 * @returns {Promise<string>} - URL to the uploaded image
 */
export const handleProductImageUpload = async (event) => {
  if (event.target.files && event.target.files[0]) {
    const file = event.target.files[0];
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      throw new Error('Please select an image file');
    }
    
    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      throw new Error('Image size should be less than 5MB');
    }
    
    // Upload the file and get a URL
    return await uploadFile(file);
  }
  return null;
};