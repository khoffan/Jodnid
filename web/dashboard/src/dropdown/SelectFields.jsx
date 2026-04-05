import { Listbox, Transition, ListboxButton, ListboxOptions, ListboxOption } from '@headlessui/react';
import { Fragment } from 'react';

const SelectField = ({ label, options, value, onChange, className = "" }) => {
  // หา Label ของค่าที่เลือกอยู่ในปัจจุบัน
  const selectedOption = options.find(opt => opt.value == value) || options[0];

  return (
    <div className={`flex flex-col flex-1 ${className}`}>
      {label && (
        <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider ml-2 mb-1">
          {label}
        </label>
      )}

      <Listbox value={value} onChange={onChange}>
        <div className="relative">
          {/* ใช้ ListboxButton โดยตรง */}
          <ListboxButton className="relative w-full bg-white border-none shadow-sm rounded-2xl px-4 py-3 text-sm font-bold text-gray-700 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-green-500/20 transition-all active:scale-95">
            <span className="block truncate">{selectedOption?.label}</span>
            <span className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-gray-400">
              {/* ไอคอนลูกศร */}
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </span>
          </ListboxButton>

          <Transition
            as={Fragment}
            leave="transition ease-in duration-100"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            {/* ใช้ ListboxOptions และ ListboxOption โดยตรง */}
            <ListboxOptions className="absolute z-50 mt-2 max-h-60 w-full overflow-auto rounded-2xl bg-white py-2 text-base shadow-xl ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
              {options.map((opt) => (
                <ListboxOption
                  key={opt.value}
                  value={opt.value}
                  className={({ focus, selected }) =>
                    `relative cursor-default select-none py-3 px-4 transition-colors ${
                      focus ? 'bg-green-50 text-green-700' : 'text-gray-900'
                    } ${selected ? 'font-black text-green-600' : 'font-medium'}`
                  }
                >
                  {({ selected }) => (
                    <div className="flex justify-between items-center">
                      <span className="block truncate">{opt.label}</span>
                      {selected && (
                        <span className="text-green-600">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </span>
                      )}
                    </div>
                  )}
                </ListboxOption>
              ))}
            </ListboxOptions>
          </Transition>
        </div>
      </Listbox>
    </div>
  );
};

export default SelectField;