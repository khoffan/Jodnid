"use client";

import Image from "next/image";
import Link from "next/link";
import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "line" | "web";
  size?: "sm" | "md" | "lg";
  navigate?: string,
  imageSrc?: string,
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  className = "",
  navigate = "#",
  imageSrc = "",
}) => {

  const baseStyles = "inline-flex items-center justify-center font-bold transition-all active:scale-95 rounded-2xl";

  const variants = {
    primary: "bg-green-600 text-white shadow-lg shadow-green-100 hover:bg-green-700",
    secondary: "bg-gray-100 text-gray-700 hover:bg-gray-200",
    line: "bg-[#06C755] text-white hover:bg-[#05b34c] shadow-xl shadow-green-100",
    web: "bg-blue-500 text-white hover:bg-blue-600 shadow-lg shadow-blue-100",
  };

  const sizes = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg md:text-xl",
  };


  return (
    <>
      {variant === "line" ? (
        <Link
          className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
          href="https://line.me/R/ti/p/@256dlaen"
          target="_blank"
        >
          <Image
            width={500}
            height={500}
            src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg"
            className="w-5 h-5 mr-2 invert"
            alt="line-icon"
          />

          {children}
        </Link>
      ) : (

        <Link
          key={navigate}
          href={navigate}
          target="_blank"
          className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        >
          {imageSrc && (
            <Image
              width={500}
              height={500}
              src={imageSrc}
              className="w-5 h-5 mr-2 invert"
              alt="line-icon"
            />
          )}
          {children}
        </Link>

      )}
    </>
  );
};

export default Button;