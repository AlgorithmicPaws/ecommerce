import React, { useState, useEffect } from 'react';
import ProductImage from '../subcomponents/ProductImage';

const ProductForm = ({ product, onSave, onCancel, categories, title }) => {
  const [formData, setFormData] = useState({
    id: null,
    name: '',
    price: '',
    stock: '',
    category: '',
    description: '',
    image: null
  });
  
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Si hay un producto existente, inicializar el formulario con sus datos
  useEffect(() => {
    if (product) {
      setFormData({
        id: product.id,
        name: product.name,
        price: product.price.toString(),
        stock: product.stock.toString(),
        category: product.category,
        description: product.description || '',
        image: product.image
      });
    }
  }, [product]);

  // Validar el formulario
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'El nombre del producto es obligatorio';
    }
    
    if (!formData.price.trim()) {
      newErrors.price = 'El precio es obligatorio';
    } else if (isNaN(parseFloat(formData.price)) || parseFloat(formData.price) <= 0) {
      newErrors.price = 'El precio debe ser un número positivo';
    }
    
    if (!formData.stock.trim()) {
      newErrors.stock = 'El stock es obligatorio';
    } else if (isNaN(parseInt(formData.stock)) || parseInt(formData.stock) < 0) {
      newErrors.stock = 'El stock debe ser un número positivo o cero';
    }
    
    if (!formData.category) {
      newErrors.category = 'La categoría es obligatoria';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Manejar cambios en los campos del formulario
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Limpiar error cuando el usuario escribe
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  // Manejar cambio de imagen
  const handleImageChange = (image) => {
    setFormData(prev => ({
      ...prev,
      image
    }));
  };

  // Manejar envío del formulario
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Convertir a números los campos numéricos
      const submittedData = {
        ...formData,
        price: parseFloat(formData.price),
        stock: parseInt(formData.stock)
      };
      
      await onSave(submittedData);
    } catch (error) {
      console.error('Error al guardar el producto:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>{title}</h2>
          <button 
            className="close-modal"
            onClick={onCancel}
            disabled={isSubmitting}
          >
            &times;
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>Nombre del Producto</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className={errors.name ? 'error' : ''}
                disabled={isSubmitting}
              />
              {errors.name && <div className="error-text">{errors.name}</div>}
            </div>
            <div className="form-group">
              <label>Categoría</label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                required
                className={errors.category ? 'error' : ''}
                disabled={isSubmitting}
              >
                <option value="">Seleccionar categoría</option>
                {categories.map((category, index) => (
                  <option key={index} value={category}>{category}</option>
                ))}
              </select>
              {errors.category && <div className="error-text">{errors.category}</div>}
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Precio ($)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                name="price"
                value={formData.price}
                onChange={handleChange}
                required
                className={errors.price ? 'error' : ''}
                disabled={isSubmitting}
              />
              {errors.price && <div className="error-text">{errors.price}</div>}
            </div>
            <div className="form-group">
              <label>Stock</label>
              <input
                type="number"
                min="0"
                name="stock"
                value={formData.stock}
                onChange={handleChange}
                required
                className={errors.stock ? 'error' : ''}
                disabled={isSubmitting}
              />
              {errors.stock && <div className="error-text">{errors.stock}</div>}
            </div>
          </div>
          <div className="form-group">
            <label>Descripción</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows="3"
              disabled={isSubmitting}
            ></textarea>
          </div>
          <div className="form-group">
            <label>Imagen del Producto</label>
            <ProductImage 
              image={formData.image}
              onChange={handleImageChange}
              disabled={isSubmitting}
            />
            <small className="form-text text-muted">
              Nota: Por ahora, las imágenes se almacenan directamente en la base de datos. En un entorno de producción, se recomienda utilizar un servicio de almacenamiento como AWS S3.
            </small>
          </div>
          <div className="modal-actions">
            <button 
              type="button" 
              className="cancel-btn"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancelar
            </button>
            <button 
              type="submit" 
              className="save-btn"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Guardando...' : product ? 'Actualizar Producto' : 'Guardar Producto'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProductForm;