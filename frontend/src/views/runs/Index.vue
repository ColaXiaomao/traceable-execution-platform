<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getRuns } from "@/api/runs";
import type { Run } from "@/types/run";
import { RUN_STATUS_MAP } from "@/types/run";
import { formatTime } from "@/utils/format";
import StatusTag from "@/components/StatusTag.vue";

const router = useRouter();
const loading = ref(false);
const runs = ref<Run[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

const fetchRuns = async () => {
  loading.value = true;
  try {
    const res = await getRuns({ page: currentPage.value, page_size: pageSize.value });
    runs.value = res.data.data;   // 取数组
    total.value = res.data.total; // 直接用后端返回的总数
  } catch {
    ElMessage.error("获取运行记录失败");
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchRuns();
};

const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchRuns();
};

onMounted(fetchRuns);
</script>

<template>
  <div>
    <div class="page-header">
      <h2>运行记录</h2>
      <el-button v-if="true" type="primary" @click="router.push('/runs/create')">+ 创建运行</el-button>
    </div>

    <el-table :data="runs" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" sortable />
      <el-table-column prop="ticket_id" label="工单ID" width="100" sortable />
      <el-table-column prop="run_type" label="类型" width="100" sortable />
      <el-table-column prop="script_id" label="脚本ID" min-width="150" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100" sortable>
        <template #default="{ row }">
          <StatusTag :status="row.status" :status-map="RUN_STATUS_MAP" />
        </template>
      </el-table-column>
      <el-table-column prop="exit_code" label="退出码" width="90" />
      <el-table-column prop="result_summary" label="结果摘要" min-width="150" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180" sortable>
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/runs/${row.id}`)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<style scoped>
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>