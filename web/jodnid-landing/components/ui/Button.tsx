"use client";

import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "line";
  size?: "sm" | "md" | "lg";
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  className = "",
  ...props
}) => {
  const baseStyles = "inline-flex items-center justify-center font-bold transition-all active:scale-95 rounded-2xl";

  const variants = {
    primary: "bg-blue-600 text-white shadow-lg shadow-blue-100 hover:bg-blue-700",
    secondary: "bg-slate-100 text-slate-700 hover:bg-slate-200",
    line: "bg-[#06C755] text-white hover:bg-[#05b34c] shadow-xl shadow-green-100",
  };

  const sizes = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg md:text-xl",
  };

  const handleLineRedirect = () => {
    if (variant === "line") {
      window.location.href = "https://line.me/R/ti/p/@256dlaen";
    }
  };

  return (
    <a
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      href={variant === "line" ? "https://line.me/R/ti/p/@256dlaen": "#how-it-works"}
    >
      {variant === "line" && (
        <img
          src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg"
          className="w-5 h-5 mr-2 invert"
          alt="line-icon"
        />
      )}
      {children}
    </a>
  );
};

export default Button;