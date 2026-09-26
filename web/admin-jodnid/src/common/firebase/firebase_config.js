import { initializeApp } from "firebase/app";
import { browserSessionPersistence, initializeAuth } from "firebase/auth";
import { config } from "../config/config";

const firebaseConfig = {
  apiKey: config.firebase.apiKey,
  authDomain: config.firebase.authDomain,
  projectId: config.firebase.projectId,
  storageBucket: config.firebase.storageBucket,
  messagingSenderId: config.firebase.messagingSenderId,
  appId: config.firebase.appId,
  measurementId: config.firebase.measurementId,
};


const app = initializeApp(firebaseConfig);
// เก็บสถานะ login แค่ใน session ของแท็บ (ค่าเริ่มต้นของ getAuth คือ IndexedDB ที่อยู่ข้ามการปิดเบราว์เซอร์)
export const auth = initializeAuth(app, { persistence: browserSessionPersistence });

