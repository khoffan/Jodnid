export default function Switch({ onChange, value }) {
  return (
    <button
      onClick={() => onChange(!value)}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20
        ${value ? "bg-blue-600" : "bg-gray-200"}
      `}
    >
      <span className="sr-only">Toggle Input Mode</span>

      {/* Knob (วงกลมสีขาว) */}
      <span
        className={`
          inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 shadow-sm
          ${value ? "translate-x-6" : "translate-x-1"}
        `}
      />
    </button>
  );
}
