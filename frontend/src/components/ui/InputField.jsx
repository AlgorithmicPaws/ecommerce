function InputField({label, type, name, placeholder}){
    return(
        <div className="w-11/12 sm:w-10/12 md:w-8/12 lg:w-full
        flex flex-col gap-3">
            <label htmlFor={name} className="text-left text-sm font-medium text-gray-700">
                {label}
            </label>
            <input
                type={type}
                id={name}
                name={name}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={placeholder}
            />
        </div>
    )
}

export default InputField;