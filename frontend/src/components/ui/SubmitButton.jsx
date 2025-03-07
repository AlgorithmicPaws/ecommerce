function SubmitButton({ text = "Enviar", className = "" }){
    return(
        <button 
      type="submit" 
      className={`text-white font-semibold py-2 px-4 rounded-md transition duration-300 cursor-pointer ${className}`}
    >
      {text}
    </button>
    )
}

export default SubmitButton;