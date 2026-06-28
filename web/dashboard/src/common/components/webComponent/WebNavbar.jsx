import React, { useState } from "react";

export default function WebNavbar({ navigate, logout }) {
  const [menuOpen, setMenuOpen] = useState(false);

  const handleNavigate = (path) => {
    setMenuOpen(false);
    navigate(path);
  };

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-10 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xl p-2 bg-green-50 text-green-600 rounded-xl">💼</span>
          <div>
            <p className="font-bold text-gray-900 text-lg tracking-tight">JodNid</p>
            <p className="text-xs text-gray-500">บัญชีรายรับ-รายจ่าย</p>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-4">
          <button
            onClick={() => handleNavigate("/add")}
            className="px-4 py-2 bg-green-600 text-white font-semibold text-sm rounded-xl hover:bg-green-700 transition flex items-center gap-1.5 shadow-sm"
          >
            <span>+</span> เพิ่มรายการ
          </button>
          <button
            onClick={() => handleNavigate("/setup")}
            className="px-4 py-2 bg-blue-600 text-white font-semibold text-sm rounded-xl hover:bg-blue-700 transition flex items-center gap-1.5 shadow-sm"
          >
            ตั้งงบประมาณ
          </button>
          <button
            onClick={() => {
              setMenuOpen(false);
              logout();
            }}
            className="bg-amber-700 text-white px-4 py-2 font-semibold text-sm rounded-xl hover:bg-amber-800 transition flex items-center gap-1.5 shadow-sm"
          >
            Logout
          </button>
        </div>

        <button
          type="button"
          className="inline-flex items-center justify-center rounded-lg border border-gray-200 bg-white p-2 text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-500 md:hidden"
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-expanded={menuOpen}
          aria-label="เปิดเมนู"
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {menuOpen ? (
              <path d="M18 6L6 18M6 6l12 12" />
            ) : (
              <>
                <path d="M3 12h18" />
                <path d="M3 6h18" />
                <path d="M3 18h18" />
              </>
            )}
          </svg>
        </button>
      </div>

      {menuOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white">
          <div className="space-y-2 px-4 py-4">
            <button
              onClick={() => handleNavigate("/add")}
              className="w-full text-left px-4 py-3 bg-green-50 text-green-700 rounded-2xl border border-green-100 font-semibold transition hover:bg-green-100"
            >
              + เพิ่มรายการ
            </button>
            <button
              onClick={() => handleNavigate("/setup")}
              className="w-full text-left px-4 py-3 bg-blue-50 text-blue-700 rounded-2xl border border-blue-100 font-semibold transition hover:bg-blue-100"
            >
              ตั้งงบประมาณ
            </button>
            <button
              onClick={() => {
                setMenuOpen(false);
                logout();
              }}
              className="w-full text-left px-4 py-3 bg-amber-50 text-amber-700 rounded-2xl border border-amber-100 font-semibold transition hover:bg-amber-100"
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
