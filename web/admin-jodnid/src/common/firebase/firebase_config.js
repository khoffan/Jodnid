import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
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
export const auth = getAuth(app);

