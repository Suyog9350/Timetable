import React, { useState } from 'react';

const UploadFile = () => {
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert('Please choose a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Corrected URL to match the FastAPI endpoint
      const response = await fetch('http://localhost:8001/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Error uploading file');
      }

      const data = await response.json();
      alert('File uploaded successfully: ' + data.message);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file, please try again.');
    }
  };

  return (
    <div>
      <h2>Upload Instructor Data</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
    </div>
  );
};

export default UploadFile;