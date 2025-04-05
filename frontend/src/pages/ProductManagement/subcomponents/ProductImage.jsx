import React, { useRef, useState, useEffect } from 'react';
import { handleProductImageUpload, resolveFileUrl } from '../../../services/fileStorageService';

const ProductImage = ({ image, onChange, disabled = false }) => {
  const fileInputRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [displayImage, setDisplayImage] = useState(null);
  
  // Resolve the image URL to a displayable URL when it changes
  useEffect(() => {
    const loadImage = async () => {
      if (image) {
        try {
          const resolvedUrl = await resolveFileUrl(image);
          setDisplayImage(resolvedUrl);
        } catch (err) {
          console.error('Error resolving image URL:', err);
          setDisplayImage(image); // Fallback to original URL
        }
      } else {
        setDisplayImage(null);
      }
    };
    
    loadImage();
  }, [image]);

  const handleFileChange = async (e) => {
    if (disabled) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      if (e.target.files && e.target.files[0]) {
        const imageUrl = await handleProductImageUpload(e);
        onChange(imageUrl);
      }
    } catch (err) {
      console.error('Error al cargar la imagen:', err);
      setError(err.message || 'Error al procesar la imagen. Por favor, intente con otra imagen.');
    } finally {
      setIsLoading(false);
    }
  };

  const triggerFileInput = () => {
    if (disabled) return;
    fileInputRef.current.click();
  };

  const clearImage = (e) => {
    e.stopPropagation();
    if (disabled) return;
    
    onChange(null);
    setDisplayImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setError(null);
  };

  return (
    <div className="image-upload-container">
      <div 
        className={`image-preview ${disabled ? 'disabled' : ''}`} 
        onClick={triggerFileInput}
        style={{ position: 'relative', cursor: disabled ? 'not-allowed' : 'pointer' }}
      >
        {isLoading ? (
          <div className="loading-spinner" style={{ margin: 'auto' }}></div>
        ) : displayImage ? (
          <div className="image-preview-container" style={{ position: 'relative', width: '100%', height: '100%' }}>
            <img src={displayImage} alt="Vista previa" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            {!disabled && (
              <button 
                type="button" 
                className="remove-image-btn"
                onClick={clearImage}
                style={{
                  position: 'absolute',
                  top: '5px',
                  right: '5px',
                  backgroundColor: 'rgba(255, 255, 255, 0.7)',
                  border: 'none',
                  borderRadius: '50%',
                  width: '25px',
                  height: '25px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  fontSize: '16px'
                }}
              >
                ×
              </button>
            )}
          </div>
        ) : (
          <div className="image-placeholder" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <span>{disabled ? 'Imagen no disponible' : 'Haz clic para subir imagen'}</span>
          </div>
        )}
      </div>
      
      {error && (
        <div className="error-text" style={{ marginTop: '5px' }}>
          {error}
        </div>
      )}
      
      <input
        type="file"
        ref={fileInputRef}
        accept="image/*"
        onChange={handleFileChange}
        style={{ display: 'none' }}
        disabled={disabled}
      />
      
      <div className="image-upload-help" style={{ marginTop: '5px', fontSize: '0.8rem', color: '#666' }}>
        Formatos aceptados: JPG, PNG, GIF. Tamaño máximo: 5MB
      </div>
    </div>
  );
};

export default ProductImage;