<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { createTicket } from "@/api/tickets";

const router = useRouter();

// 表单数据
const formData = ref({
  title: "",
  description: ""  // 👈 改了
});

// 提交工单
const handleSubmit = async () => {
  if (!formData.value.title || !formData.value.description) {  // 👈 改了
    ElMessage.warning("请填写标题和描述");
    return;
  }

  try {
    const res = await createTicket(formData.value);
    ElMessage.success("工单创建成功！");
    router.push({ name: "TicketList" });
  } catch (error) {
    console.error("创建工单失败", error);
    ElMessage.error("创建失败，请重试");
  }
};
</script>

<template>
  <div class="ticket-create">
    <el-card>
      <el-form :model="formData" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="formData.title" placeholder="请输入标题" />
        </el-form-item>

        <el-form-item label="描述">  <!-- 👈 改了 -->
          <el-input
            type="textarea"
            v-model="formData.description" 
            placeholder="请输入描述"
            :rows="5"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit">提交</el-button>
          <el-button @click="router.push({ name: 'TicketList' })">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>