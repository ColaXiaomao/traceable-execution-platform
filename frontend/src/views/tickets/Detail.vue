<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getTicket, approveTicket, type Ticket } from "@/api/tickets";
import { useUserStore } from "@/stores/user";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const ticket = ref<Ticket | null>(null);

const statusMap: Record<string, { label: string; type: string }> = {
  draft:     { label: "草稿",   type: "info" },
  submitted: { label: "待审批", type: "warning" },
  approved:  { label: "已通过", type: "success" },
  rejected:  { label: "已拒绝", type: "danger" }
};

const fetchTicket = async () => {
  loading.value = true;
  try {
    const res = await getTicket(Number(route.params.id));
    ticket.value = res.data;
  } catch {
    ElMessage.error("获取工单详情失败");
  } finally {
    loading.value = false;
  }
};

const handleApprove = async () => {
  if (!ticket.value) return;
  await ElMessageBox.confirm(`确认通过工单「${ticket.value.title}」？`, "提示", {
    confirmButtonText: "确认",
    cancelButtonText: "取消",
    type: "warning"
  });
  try {
    await approveTicket(ticket.value.id);
    ElMessage.success("审批成功");
    fetchTicket();
  } catch {
    ElMessage.error("审批失败");
  }
};

const formatTime = (time: string) =>
  new Date(time).toLocaleString("zh-CN", { hour12: false });

onMounted(fetchTicket);
</script>

<template>
  <div v-loading="loading">
    <div class="page-header">
      <el-button link @click="router.push('/tickets')">← 返回列表</el-button>
      <h2>工单详情</h2>
      <el-button
        v-if="userStore.userInfo?.is_admin && ticket?.status === 'submitted'"
        type="success"
        @click="handleApprove"
      >
        通过审批
      </el-button>
    </div>

    <el-card v-if="ticket">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="工单ID">{{ ticket.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusMap[ticket.status]?.type">
            {{ statusMap[ticket.status]?.label || ticket.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{ ticket.title }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ ticket.description || "无" }}
        </el-descriptions-item>
        <el-descriptions-item label="资产ID">{{ ticket.asset_id }}</el-descriptions-item>
        <el-descriptions-item label="提交人ID">{{ ticket.created_by_id }}</el-descriptions-item>
        <el-descriptions-item label="审批人ID">{{ ticket.approved_by_id || "未审批" }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(ticket.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(ticket.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

h2 {
  margin: 0;
  font-size: 20px;
  flex: 1;
}
</style>