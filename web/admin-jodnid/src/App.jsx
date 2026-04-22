import { Routes, Route } from "react-router";
import { SystemConfiguration } from "./features/systemConfiguration/pages/SystemConfiguration";
import { AdminNavbar } from "./common/components/AdminNavbar";
const element = (
  <Routes>
    <Route path="/" element={<SystemConfiguration />} />
  </Routes>
);

export default function App() {
  return (
    <div>
      <AdminNavbar />
      {element}
    </div>
  );
}
