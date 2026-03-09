<script setup lang="ts">
import { reactive } from "vue";
import { useRouter } from "vue-router";
import { createTicket } from "@/api/tickets";
import { ElMessage } from "element-plus";

const router = useRouter();

const form = reactive({
  title: "",
  description: ""
});

const submit = async () => {
  await createTicket(form);
  ElMessage.success("创建成功");
  router.push("/tickets");
};
</script>

<template>
  <div>
    <h2>创建工单</h2>

    <el-form label-width="100px">

      <el-form-item label="标题">
        <el-input v-model="form.title" />
      </el-form-item>

      <el-form-item label="描述">
        <el-input
          type="textarea"
          v-model="form.description"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submit">
          提交
        </el-button>
      </el-form-item>

    </el-form>
  </div>
</template>