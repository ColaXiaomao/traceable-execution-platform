<script setup lang="ts">
import { useTicket } from "./utils/hook";
import { PureTable } from "@pureadmin/table";

const { loading, dataList, pagination, handleApprove } = useTicket();

// 定义表格列，对接后端字段
const columns: TableColumnList = [
  { label: "ID", prop: "id", width: 70 },
  { label: "标题", prop: "title" },
  { label: "状态", prop: "status" },
  {
    label: "操作",
    fixed: "right",
    slot: "operation"
  }
];
</script>

<template>
  <div class="main">
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
          @click="handleApprove(row)"
          v-if="row.status === 'pending'"
        >
          通过审批
        </el-button>
      </template>
    </pure-table>
  </div>
</template>