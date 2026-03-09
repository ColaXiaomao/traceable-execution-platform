<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getTicket, updateTicket, Ticket } from "@/api/tickets";

const route = useRoute();
const router = useRouter();
const ticketId = route.params.id as string;

const loading = ref(false);
const ticket = ref<Ticket | null>(null);
const title = ref("");
const description = ref("");

const fetchTicket = async () => {
  loading.value = true;
  try {
    const res = await getTicket(ticketId);
    ticket.value = res.data;
    title.value = ticket.value.title;
    description.value = ticket.value.description || "";
  } catch (error) {
    console.error("获取工单失败", error);
  } finally {
    loading.value = false;
  }
};

const handleUpdate = async () => {
  loading.value = true;
  try {
    await updateTicket(ticketId, { title: title.value, description: description.value });
    ElMessage.success("更新成功");
    router.push("/ticket/index");
  } catch (error) {
    console.error("更新失败", error);
    ElMessage.error("更新失败");
  } finally {
    loading.value = false;
  }
};

onMounted(fetchTicket);
</script>

<template>
  <div class="main">
    <el-form label-width="100px">
      <el-form-item label="标题">
        <el-input v-model="title"></el-input>
      </el-form-item>
      <el-form-item label="描述">
        <el-input type="textarea" v-model="description"></el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleUpdate">
          更新
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>