export function formatLectureDate(date, time) {
  if (!date) return "Date not set";
  const value = new Date(`${date}T${time || "00:00:00"}`);
  if (Number.isNaN(value.getTime())) return `${date} ${time || ""}`.trim();

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(value);
}

export function formatCalendarLabel(dateValue) {
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "2-digit",
    month: "short",
  }).format(dateValue);
}

export function startOfWeek(dateValue) {
  const date = new Date(dateValue);
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + diff);
  date.setHours(0, 0, 0, 0);
  return date;
}

export function addDays(dateValue, days) {
  const next = new Date(dateValue);
  next.setDate(next.getDate() + days);
  return next;
}

export function isSameDay(dateA, dateB) {
  return dateA.getFullYear() === dateB.getFullYear()
    && dateA.getMonth() === dateB.getMonth()
    && dateA.getDate() === dateB.getDate();
}

export function getApiError(error, fallback) {
  const detail = error?.response?.data?.detail;

  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((item) => item.msg || fallback).join(" | ");
  }

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  return fallback;
}

export function getSubjectColor(subject = "") {
  const palette = [
    "#f3c26b",
    "#d88c6a",
    "#8ec5a4",
    "#7fb0d8",
    "#c7a6e8",
    "#e6a6b9",
  ];
  const normalized = subject.trim().toLowerCase();
  let hash = 0;
  for (let index = 0; index < normalized.length; index += 1) {
    hash = normalized.charCodeAt(index) + ((hash << 5) - hash);
  }
  return palette[Math.abs(hash) % palette.length];
}

export function buildIcsFile(items, filename = "schedule.ics") {
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Smart Classroom//Schedule Export//EN",
  ];

  items.forEach((item) => {
    const start = new Date(`${item.date}T${item.time || "00:00:00"}`);
    if (Number.isNaN(start.getTime())) return;
    const end = new Date(start.getTime() + ((item.duration || 80) * 60 * 1000));
    const format = (value) => value.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
    lines.push("BEGIN:VEVENT");
    lines.push(`UID:${item.lecture_id ?? item.id}-${item.date}-${item.time}@smartclassroom`);
    lines.push(`DTSTAMP:${format(new Date())}`);
    lines.push(`DTSTART:${format(start)}`);
    lines.push(`DTEND:${format(end)}`);
    lines.push(`SUMMARY:${item.title}`);
    lines.push(`DESCRIPTION:${item.subject}`);
    lines.push("END:VEVENT");
  });

  lines.push("END:VCALENDAR");
  const blob = new Blob([lines.join("\r\n")], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function buildCsvFile(rows, filename = "report.csv") {
  if (!rows.length) return;

  const headers = Object.keys(rows[0]);
  const escapeValue = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const lines = [
    headers.join(","),
    ...rows.map((row) => headers.map((header) => escapeValue(row[header])).join(",")),
  ];

  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function openPrintableReport(rows, title = "Smart Classroom Report") {
  if (!rows.length) return;

  const headers = Object.keys(rows[0]);
  const headerLabels = {
    full_name: "Student",
    group_name: "Group",
    course_name: "Course",
    subject: "Subject",
    attendance_rate: "Attendance",
    average_grade: "Average",
    final_score: "Final",
    risk_status: "Status",
  };

  const tableHead = headers
    .map((header) => `<th>${headerLabels[header] || header}</th>`)
    .join("");

  const tableRows = rows
    .map((row) => (
      `<tr>${headers.map((header) => `<td>${String(row[header] ?? "")}</td>`).join("")}</tr>`
    ))
    .join("");

  const printWindow = window.open("", "_blank", "width=1200,height=800");
  if (!printWindow) return;

  printWindow.document.write(`<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>${title}</title>
    <style>
      body {
        font-family: Georgia, "Times New Roman", serif;
        margin: 32px;
        color: #2d2014;
      }
      h1 {
        margin: 0 0 8px;
        font-size: 28px;
      }
      p {
        margin: 0 0 20px;
        color: #6b5238;
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      th, td {
        border: 1px solid #d8c6ab;
        padding: 10px 12px;
        text-align: left;
        font-size: 13px;
      }
      th {
        background: #f3e4c9;
        color: #5b3c1f;
      }
      tr:nth-child(even) td {
        background: #fcf8f1;
      }
      @media print {
        body {
          margin: 12mm;
        }
      }
    </style>
  </head>
  <body>
    <h1>${title}</h1>
    <p>Generated from Smart Classroom Management System</p>
    <table>
      <thead>
        <tr>${tableHead}</tr>
      </thead>
      <tbody>
        ${tableRows}
      </tbody>
    </table>
  </body>
</html>`);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
}
