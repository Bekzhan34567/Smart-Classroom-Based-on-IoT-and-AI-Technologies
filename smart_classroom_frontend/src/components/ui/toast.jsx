import { useEffect } from "react";
import { X } from "lucide-react";

export function Toast({ message, type = "info", onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = {
    success: "bg-green-500",
    error: "bg-red-500",
    warning: "bg-yellow-500",
    info: "bg-blue-500",
  }[type];

  return (
    <div className={`fixed top-4 right-4 ${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 z-50 animate-in slide-in-from-right duration-300`}>
      <span className="text-sm">{message}</span>
      <button
        onClick={onClose}
        className="hover:bg-white/20 rounded p-1 transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
