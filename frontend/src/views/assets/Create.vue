<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { createAsset } from "@/api/assets";

const router = useRouter();
const formRef = ref<FormInstance>();
const loading = ref(false);

const form = ref({
  name: "",
  asset_type: "",
  serial_number: "",
  location: "",
  description: ""
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入资产名称", trigger: "blur" }],
  asset_type: [{ required: true, message: "请输入资产类型", trigger: "blur" }]
};

const onSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async valid => {
    if (!valid) return;
    loading.value = true;
    try {
      await createAsset(form.value);
      ElMessage.success("资产创建成功");
      router.push("/assets");
    } catch {
      ElMessage.error("资产创建失败");
    } finally {
      loading.value = false;
    }
  });
};
</script>

<template>
  <div>
    <div class="page-header">
      <h2>创建资产</h2>
    </div>

    <el-card>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入资产名称" />
        </el-form-item>
        <el-form-item label="类型" prop="asset_type">
          <el-input v-model="form.asset_type" placeholder="例如：服务器、网络设备" />
        </el-form-item>
        <el-form-item label="序列号" prop="serial_number">
          <el-input v-model="form.serial_number" placeholder="请输入序列号（选填）" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="form.location" placeholder="请输入资产位置（选填）" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入描述（选填）" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">创建资产</el-button>
          <el-button @click="router.push('/assets')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.page-header { margin-bottom: 20px; }
h2 { margin: 0; font-size: 20px; }
.el-card { max-width: 600px; }
</style>