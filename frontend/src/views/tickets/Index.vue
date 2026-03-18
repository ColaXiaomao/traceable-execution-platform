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
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

const fetchTickets = async () => {
  loading.value = true;
  try {
    const skip = (currentPage.value - 1) * pageSize.value;
    const res = await getTickets({ skip, limit: pageSize.value });
    tickets.value = res.data;
    // 后端没有返回total，用当前数量判断是否还有更多
    total.value = res.data.length < pageSize.value
      ? skip + res.data.length
      : skip + res.data.length + 1;
  } catch {
    ElMessage.error("获取工单列表失败");
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchTickets();
};

const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchTickets();
};

const handleApprove = async (row: Ticket) => {
  await ElMessageBox.confirm(`确认通过工单「${row.title}」？`, "提示", {
    confirmButtonText: "确认", cancelButtonText: "取消", type: "warning"
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
      <el-button type="primary" @click="router.push('/tickets/create')">+ 创建工单</el-button>
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