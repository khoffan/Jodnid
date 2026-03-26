import React, { useState, useEffect } from 'react';
import liff from '@line/liff';
import Dashboard from './pages/Dashboard';

function App() {
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    liff.init({ liffId: "2009591013-HEgnyCkE" }).then(() => {
      if (liff.isLoggedIn()) {
        const profile = liff.getContext();
        setUserId(profile.userId);
      } else {
        liff.login();
      }
    });
  }, []);

  return (
    <div className="max-w-md mx-auto min-h-screen shadow-2xl bg-white">
      {userId ? <Dashboard userId={userId} /> : <div className="p-10">กำลังยืนยันตัวตน...</div>}
    </div>
  );
}

export default App;