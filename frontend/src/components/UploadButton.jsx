import React, { useRef } from 'react';
import Button from './Button';

const UploadButton = ({ onUpload, label = "Upload Image", accept = "image/*" }) => {
  const inputRef = useRef(null);

  const handleClick = () => inputRef.current.click();

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files[0]);
    }
  };

  return (
    <>
      <Button onClick={handleClick}>{label}</Button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        style={{ display: 'none' }}
      />
    </>
  );
};

export default UploadButton;
