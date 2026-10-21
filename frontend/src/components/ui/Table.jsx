import React from "react";

export default function Table({
  headers = [],
  children,
  className = "",
}) {
  return (
    <div className={`w-full overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm ${className}`}>
      <table className="w-full text-left border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50/75">
            {headers.map((header, idx) => (
              <th
                key={idx}
                className="py-3.5 px-4 font-semibold text-slate-700 text-xs tracking-wider uppercase"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 text-slate-600">
          {children}
        </tbody>
      </table>
    </div>
  );
}
