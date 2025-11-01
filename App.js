import React from 'react';
import UploadForm from './components/UploadForm';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Student Defaulter Classification System
          </h1>
          <p className="text-gray-600">
            Upload student attendance data to classify defaulters and non-defaulters
          </p>
        </header>
        <UploadForm />
      </div>
    </div>
  );
}

export default App;

