const Alert = ({ message, type }) => {
    const color = type === "error" ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700";
    return (
      <div className={`p-3 rounded-md my-2 text-sm font-medium ${color}`}>
        {message}
      </div>
    );
  };
  
  export default Alert;
  