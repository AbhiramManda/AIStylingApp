const Button = ({ text, onClick, type = "button", className = "" }) => {
    return (
      <button
        type={type}
        onClick={onClick}
        className={`bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition ${className}`}
      >
        {text}
      </button>
    );
  };
  
  export default Button;
  