import { useEffect, useState } from "react";
import { Settings, RefreshCw, Plus, Loader2 } from "lucide-react";
import { StatusCards } from "../components/StatusCard";
import { ConfigTable } from "../components/ConfigTable";
import { ConfigModal } from "../components/ConfigModel";
import { CreateConfigModal } from "../components/CreateConfigModal";
import useConfigStore from "../store/system-config.store";

export const SystemConfiguration = () => {
  const [isConfigModalOpen, setConfigModalOpen] = useState(false);
  const [isCreateModalOpen, setCreateModalOpen] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const { configs, fetchConfigs, toggleConfig } = useConfigStore();

  useEffect(() => {
    fetchConfigs();
  }, [fetchConfigs]);

  const handleEdit = (config) => {
    setSelectedConfig(config);
    setConfigModalOpen(true);
  };

  const handleSave = async (updatedData) => {
    // ยิง API PATCH/POST ที่นี่
    console.log("Saving data...", updatedData);
    setConfigModalOpen(false);
  };

  const handleToggleConfig = async (key, newValue) => {
    // สมมติว่าใน store มีฟังก์ชัน updateConfigByKey
    const result = await toggleConfig(key, newValue);

    if (!result.success) {
      alert("ไม่สามารถอัปเดตสถานะได้: " + result.error);
    }
  };

  if (!configs) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="animate-spin text-blue-500 w-12 h-12" />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Settings className="text-blue-500" /> JodNid Administrator
          </h1>
          <p className="text-gray-500 text-sm mt-1">จัดการระบบหลังบ้าน</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {}}
            className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors font-medium rounded-lg text-sm"
          >
            <RefreshCw size={16} />
            Refresh Cache
          </button>
          <button
            onClick={() => setCreateModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white hover:bg-blue-600 transition-colors shadow-md shadow-blue-500/30 font-medium rounded-lg text-sm"
          >
            <Plus size={16} />
            Create
          </button>
        </div>
      </div>

      <StatusCards />

      {/* Table Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-1">
        <ConfigTable
          configs={configs ?? []}
          onEdit={handleEdit}
          onToggle={handleToggleConfig}
        />
      </div>

      <ConfigModal
        isOpen={isConfigModalOpen}
        onOpenChange={setConfigModalOpen}
        selectedConfig={selectedConfig}
        onSave={handleSave}
      />

      <CreateConfigModal
        isOpen={isCreateModalOpen}
        onOpenChange={setCreateModalOpen}
      />
    </div>
  );
};
