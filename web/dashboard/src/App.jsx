import { useEffect } from "react";
import { useNavigate } from "react-router";
import WebPage from "./pages/webPage";
import LiffPage from "./pages/LiffPage";
import { useWebAuthStore } from "./features/webapp/auth/store/web_auth.store";

function App() {
  const { initApp, isWebApp, userId } = useWebAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    initApp(navigate);
  }, [initApp, navigate]);

  return (
    <>{isWebApp ? <WebPage userId={userId} /> : <LiffPage userId={userId} />}</>
  );
}

export default App;
