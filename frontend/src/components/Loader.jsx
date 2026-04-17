import React from 'react';
import './Loader.css';

const Loader = ({ fullScreen = true, text = "Loading..." }) => {
  return (
    <div className={`loader-container ${fullScreen ? 'loader-fullscreen' : ''}`}>
      <div className="loader-content">
        <div className="loader-logo-wrapper">
          <div className="spinner-ring"></div>
          <img src="/vignan_loader.png" alt="Vignan Loader" className="loader-logo pulse" />
        </div>
        {text && <p className="loader-text">{text}</p>}
      </div>
    </div>
  );
};

export default Loader;
