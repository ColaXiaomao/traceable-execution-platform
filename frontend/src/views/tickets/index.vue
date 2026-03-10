<script setup lang="ts">
import { ref, onMounted } from "vue";
import { PureTable } from "@pureadmin/table";
import { ElMessage } from "element-plus";
import { getTicketList, approveTicket, getCurrentUser } from "@/api/tickets";
import type { Ticket } from "@/api/tickets";

const loading = ref(false);
const dataList = ref<any[]>([]);
const pagination = ref({ current: 1, pageSize: 10, total: 0 });
const isAdmin = ref(false);

// 请求列表
const fetchList = async () => {
  loading.value = true;
  try {
    const res = await getTicketList();
    dataList.value = res as any;
    pagination.value.total = (res as any).length;
  } catch (err) {
    console.error("获取工单列表失败", err);
  } finally {
    loading.value = false;
  }
};

// 审批操作
const handleApprove = async (row: any) => {
  try {
    await approveTicket(row.id);
    ElMessage.success("审批成功");
    fetchList();
  } catch (error) {
    console.error("审批失败", error);
    ElMessage.error("审批失败");
  }
};

onMounted(async () => {
  const user = await getCurrentUser() as any;
  isAdmin.value = user.is_admin;
  fetchList();
});

const columns = [
  { label: "ID", prop: "id", width: 70 },
  { label: "标题", prop: "title" },
  { label: "描述", prop: "description", slot: "desc" }, // 👈 用slot
  { label: "提交人", prop: "created_by_id" },
  { label: "状态", prop: "status" },
  {
    label: "操作",
    fixed: "right",
    slot: "operation",
    width: 120
  }
];
</script>

<template>
  <div class="ticket-list">
    <pure-table
      row-key="id"
      adaptive
      :loading="loading"
      :data="dataList"
      :columns="columns"
      :pagination="pagination"
    >
      <template #desc="{ row }">
        <el-tooltip
          :content="row.description"
          placement="top"
          :disabled="!row.description || row.description.length <= 8"
        >
          <span>
            {{ row.description
              ? row.description.length > 8
                ? row.description.slice(0, 8) + '...'
                : row.description
              : '-' }}
          </span>
        </el-tooltip>
      </template>

      <template #operation="{ row }">
        <el-button
          link
          type="primary"
          size="small"
          @click="handleApprove(row)"
          v-if="isAdmin && row.status === 'submitted'"
        >
          通过审批
        </el-button>
      </template>
    </pure-table>
  </div>
</template>