<script setup lang="ts">
import { ref, onMounted } from "vue";
import { PureTable } from "@pureadmin/table";
import { ElMessage } from "element-plus";
import { getTicketList, approveTicket } from "@/api/tickets";
import type { Ticket } from "@/api/tickets"// 注意路径

const loading = ref(false);
const dataList = ref<any[]>([]);
const pagination = ref({ current: 1, pageSize: 10, total: 0 });

// 请求列表
const fetchList = async () => {
  loading.value = true;
  try {
    const res = await getTicketList({
      page: pagination.value.current,
      pageSize: pagination.value.pageSize
    });

    // res 是 { list: Ticket[], total: number }，所以要解构
    dataList.value = res.list;
    pagination.value.total = res.total;
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
    fetchList(); // 审批后刷新
  } catch (error) {
    console.error("审批失败", error);
    ElMessage.error("审批失败");
  }
};

onMounted(fetchList);

const columns = [
  { label: "ID", prop: "id", width: 70 },
  { label: "标题", prop: "title" },
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
      <template #operation="{ row }">
        <el-button
          link
          type="primary"
          size="small"
          @click="handleApprove(row)"
          v-if="row.status === 'pending'"
        >
          通过审批
        </el-button>
      </template>
    </pure-table>
  </div>
</template>