export const dashboardCards = [
  { label: "Active Sessions", value: "24", detail: "Connected users now" },
  { label: "Server Load", value: "18%", detail: "CPU usage today" },
  { label: "Pending Tasks", value: "7", detail: "Items waiting for review" },
];

export const adminItems = [
  {
    title: "System Audit",
    status: "Completed",
    description: "ตรวจสอบระบบล่าสุดเมื่อ 2 ชั่วโมงก่อน",
  },
  {
    title: "Backup Status",
    status: "Ready",
    description: "สำรองข้อมูลอัตโนมัติทุกวันเวลา 02:00 น.",
  },
  { title: "Cache Flush", status: "Available", description: "ล้างแคชระบบเพื่ออัปเดตค่าทันที" },
];

export const mockConfigs = [
  {
    key: "feature_x_enabled",
    name: "Feature X",
    value: "true",
    value_type: "boolean",
    description: "เปิดหรือปิดฟีเจอร์ X สำหรับผู้ใช้ใหม่",
  },
  {
    key: "page_size",
    name: "Default Page Size",
    value: "25",
    value_type: "int",
    description: "จำนวนรายการที่แสดงในตารางโดยปริยาย",
  },
  {
    key: "welcome_message",
    name: "Welcome Message",
    value: "Hello from JodNid",
    value_type: "string",
    description: "ข้อความต้อนรับผู้ใช้เมื่อเข้าใช้งานระบบ",
  },
];

export const mockLogs = [
  {
    id: 1,
    timestamp: "2026-06-13 10:45:12",
    level: "INFO",
    module: "auth",
    message: "ผู้ใช้เข้าสู่ระบบเรียบร้อยแล้ว",
    payload: { userId: "Uca724fb6c9bffd7d8606e754e160eac3" },
    stack_trace: null,
  },
  {
    id: 2,
    timestamp: "2026-06-13 09:34:50",
    level: "WARN",
    module: "cache",
    message: "Cache miss for /api/administrator/all",
    payload: { route: "/api/administrator/all" },
    stack_trace: null,
  },
  {
    id: 3,
    timestamp: "2026-06-13 08:12:18",
    level: "ERROR",
    module: "database",
    message: "Connection timeout to read master DB",
    payload: { host: "db.prod.internal" },
    stack_trace:
      "TimeoutError: connect ETIMEDOUT\n    at TCPConnectWrap.afterConnect [as oncomplete] (node:net:1180:16)",
  },
];

export const mockUsers = [
  {
    id: "U001",
    name: "สุชาติ แซ่ลิ้ม",
    email: "suchart@example.com",
    role: "Admin",
    status: "Active",
  },
  {
    id: "U002",
    name: "พิมพ์ชนก อินทร์ทา",
    email: "pimchanok@example.com",
    role: "Editor",
    status: "Pending",
  },
  {
    id: "U003",
    name: "ธนกร วงศ์สวัสดิ์",
    email: "thanakorn@example.com",
    role: "Viewer",
    status: "Active",
  },
];
