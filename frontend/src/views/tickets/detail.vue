<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { getTicket, approveTicket } from "@/api/tickets";
import { ElMessage } from "element-plus";

const route = useRoute();

const ticket = ref<any>({});

const fetchTicket = async () => {
  const id = Number(route.params.id);
  const res = await getTicket(id);
  ticket.value = res.data;
};

const approve = async () => {
  await approveTicket(ticket.value.id);
  ElMessage.success("审批成功");
  fetchTicket();
};

onMounted(() => {
  fetchTicket();
});
</script>

<template>
  <div>
    <h2>工单详情</h2>

    <el-descriptions border>

      <el-descriptions-item label="ID">
        {{ ticket.id }}
      </el-descriptions-item>

      <el-descriptions-item label="标题">
        {{ ticket.title }}
      </el-descriptions-item>

      <el-descriptions-item label="描述">
        {{ ticket.description }}
      </el-descriptions-item>

      <el-descriptions-item label="状态">
        {{ ticket.status }}
      </el-descriptions-item>

    </el-descriptions>

    <el-button
      type="success"
      style="margin-top:20px"
      @click="approve"
    >
      审批
    </el-button>

  </div>
</template>