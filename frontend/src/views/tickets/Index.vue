<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getTickets, approveTicket } from "@/api/tickets";
import type { Ticket } from "@/types/ticket";
import { TICKET_STATUS_MAP } from "@/types/ticket";
import { useUserStore } from "@/stores/user";
import { formatTime } from "@/utils/format";
import StatusTag from "@/components/StatusTag.vue";

const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const tickets = ref<Ticket[]>([]);

const fetchTickets = async () => {
  loading.value = true;
  try {
    const res = await getTickets();
    tickets.value = res.data;
  } catch {
    ElMessage.error("获取工单列表失败");
  } finally {
    loading.value = false;
  }
};

const handleApprove = async (row: Ticket) => {
  await ElMessageBox.confirm(`确认通过工单「${row.title}」？`, "提示", {
    confirmButtonText: "确认",
    cancelButtonText: "取消",
    type: "warning"
  });
  try {
    await approveTicket(row.id);
    ElMessage.success("审批成功");
    fetchTickets();
  } catch {
    ElMessage.error("审批失败");
  }
};

onMounted(fetchTickets);
</script>

<template>
  <div>
    <div class="page-header">
      <h2>工单列表</h2>
      <el-button type="primary" @click="router.push('/tickets/create')">
        + 创建工单
      </el-button>
    </div>

    <el-table :data="tickets" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" sortable />
      <el-table-column prop="title" label="标题" min-width="150" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100" sortable>
        <template #default="{ row }">
          <StatusTag :status="row.status" :status-map="TICKET_STATUS_MAP" />
        </template>
      </el-table-column>
      <el-table-column prop="created_by_id" label="提交人" width="100" sortable />
      <el-table-column prop="created_at" label="创建时间" width="180" sortable>
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/tickets/${row.id}`)">查看</el-button>
          <el-button
            v-if="userStore.userInfo?.is_admin && row.status === 'submitted'"
            link type="success"
            @click="handleApprove(row)"
          >审批</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>