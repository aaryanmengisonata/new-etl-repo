import React from 'react';
import { Loader2 } from 'lucide-react';

export function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  isLoading, 
  icon: Icon,
  className = '',
  ...props 
}) {
  const baseStyles = "relative inline-flex items-center justify-center rounded-xl font-black uppercase tracking-[0.2em] transition-all duration-300 transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-500/20",
    secondary: "bg-slate-100 text-slate-700 hover:bg-slate-200",
    danger: "bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-500/20",
    ghost: "bg-transparent text-slate-500 hover:text-slate-900 border border-slate-200 hover:border-slate-300"
  };

  const sizes = {
    sm: "px-6 py-2 text-[8px]",
    md: "px-8 py-3 text-[10px]",
    lg: "px-12 py-4 text-[12px]"
  };

  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={isLoading}
      {...props}
    >
      {isLoading ? (
        <span className="flex items-center gap-2"><Loader2 size={14} className="animate-spin" /> Loading</span>
      ) : (
        <span className="flex items-center gap-2">
          {Icon && <Icon size={14} />}
          {children}
        </span>
      )}
    </button>
  );
}
