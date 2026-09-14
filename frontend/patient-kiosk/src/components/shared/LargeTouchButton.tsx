import React from "react";

export function LargeTouchButton({ 
  children, 
  onClick, 
  variant = "primary",
  type = "button",
  disabled = false,
  className = ""
}: { 
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "outline";
  type?: "button" | "submit" | "reset";
  disabled?: boolean;
  className?: string;
}) {
  const baseClasses = "flex items-center justify-center w-full px-8 py-6 rounded-2xl text-2xl font-semibold transition-colors duration-200 shadow-sm active:scale-95 touch-manipulation disabled:opacity-50 disabled:pointer-events-none";
  
  const variants = {
    primary: "bg-primary text-primary-foreground hover:bg-primary/90",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    outline: "border-2 border-border bg-transparent hover:bg-muted text-foreground",
  };

  return (
    <button 
      type={type}
      onClick={onClick} 
      className={`${baseClasses} ${variants[variant]} ${className}`}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
