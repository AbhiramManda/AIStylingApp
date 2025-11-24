const InputField = ({ label, type, name, value, onChange, placeholder }) => {
    return (
      <div className="flex flex-col mb-4">
        <label className="text-sm font-medium text-gray-700 mb-1">{label}</label>
        <input
          type={type}
          name={name}
          value={value}
          placeholder={placeholder}
          onChange={onChange}
          className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    );
  };
  
  export default InputField;
  
