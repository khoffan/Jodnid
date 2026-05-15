import { create } from "zustand";
import api from "../../../../common/lib/api";

export const useWebTransaction = create(() => ({
  createTransaction: async (transaction) => {
    try {
      console.log("Creating transaction:", transaction);
      const token = sessionStorage.getItem("id_token");
      if (!token) {
        console.error("No ID token found in sessionStorage");
        return false;
      }
      const res = await api.post("/api/web/transaction/add", transaction, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (res.data.detail.success) {
        return true;
      }
      return false;
    } catch (error) {
      console.error("Error creating transaction:", error);
      return false;
    }
  },
}));
