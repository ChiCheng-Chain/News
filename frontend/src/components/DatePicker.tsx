interface DatePickerProps {
  value: string   // YYYY-MM-DD
  onChange: (date: string) => void
}

export function DatePicker({ value, onChange }: DatePickerProps) {
  const today = new Date().toISOString().split('T')[0]
  return (
    <div className="flex items-center gap-3">
      <input
        type="date"
        value={value}
        max={today}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      {value !== today && (
        <button
          onClick={() => onChange(today)}
          className="text-xs text-blue-500 hover:underline"
        >
          回到今天
        </button>
      )}
    </div>
  )
}
