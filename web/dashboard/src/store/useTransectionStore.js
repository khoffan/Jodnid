import { create } from 'zustand';
import axios from 'axios';

const useTransactionStore = create((set) => ({
  transactions: [],
  summary: {},
  totalAmount: 0,
  loading: false,
  
  fetchDashboard: async (userId) => {
    set({ loading: true });
    try {
      const response = await axios.get(`https://3939-1-47-7-52.ngrok-free.app/api/dashboard/${userId}`);
      set({ 
        transactions: response.data.transactions,
        summary: response.data.summary,
        totalAmount: response.data.total_amount,
        loading: false 
      });
    } catch (error) {
      console.error("Fetch error:", error);
      set({ loading: false });
    }
  },
}));

export default useTransactionStore;