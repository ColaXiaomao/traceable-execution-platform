<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getRuns, type Run } from "@/api/runs";

const router = useRouter();
const loading = ref(false);
const runs = ref<Run[]>([]);

const statusMap: Record<string, { label: string; type: string }> = {
  pending:  { label: "等待中", type: "info" },
  running:  { label: "执行中", type: "primary" },
  done:     { label: "已完成", type: "success" },
  failed:   { label: "失败",   type: "danger" }
};

const fetchRuns = async () => {
  loading.value = true;
  try {
    const res = await getRuns();
    runs.value = res.data;
  } catch {
    ElMessage.error("获取运行记录失败");
  } finally {
    loading.value = false;
  }
};

const formatTime = (time: string) =>
  new Date(time).toLocaleString("zh-CN", { hour12: false });

onMounted(fetchRuns);
</script>

<template>
  <div>
    <div class="page-header">
      <h2>运行记录</h2>
    </div>

    <el-table :data="runs" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" sortable />
      <el-table-column prop="ticket_id" label="工单ID" width="100" sortable />
      <el-table-column prop="run_type" label="类型" width="100" sortable />
      <el-table-column prop="script_id" label="脚本ID" min-width="150" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100" sortable>
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type">
            {{ statusMap[row.status]?.label || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="exit_code" label="退出码" width="90" />
      <el-table-column prop="result_summary" label="结果摘要" min-width="150" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180" sortable>
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/runs/${row.id}`)">
            查看
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
h2 { margin: 0; font-size: 20px; }
</style>