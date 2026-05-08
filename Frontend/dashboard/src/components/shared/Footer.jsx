import React from 'react';
import sonataLogo from '../../assets/Images/Sonata_Software_Logo.svg'; 

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-100 h-14 flex items-center">
      <div className="w-full max-w-7xl mx-auto px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] font-bold uppercase tracking-widest text-slate-500">
        {/* Left */}
        <div className="flex items-center gap-3">
          <img 
            src={sonataLogo} 
            alt="Sonata Logo" 
            className="h-5 object-contain opacity-80" 
          />
          <span className="opacity-70">
            Powered by Sonata Software Limited
          </span>
        </div>

        {/* Right */}
        <div className="opacity-70">
          © Sonata Software. All rights reserved {currentYear}.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
