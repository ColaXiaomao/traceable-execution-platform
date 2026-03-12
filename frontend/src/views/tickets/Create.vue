<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { createTicket } from "@/api/tickets";
import { getAssets, type Asset } from "@/api/assets";

const router = useRouter();
const formRef = ref<FormInstance>();
const loading = ref(false);
const assets = ref<Asset[]>([]);

const form = ref({
  title: "",
  description: "",
  asset_id: undefined
});

const rules: FormRules = {
  title: [{ required: true, message: "请输入工单标题", trigger: "blur" }],
  asset_id: [{ required: true, message: "请选择资产", trigger: "change" }]
};

const fetchAssets = async () => {
  try {
    const res = await getAssets();
    assets.value = res.data;
  } catch {
    ElMessage.error("获取资产列表失败");
  }
};

const onSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async valid => {
    if (!valid) return;
    loading.value = true;
    try {
      await createTicket(form.value);
      ElMessage.success("工单创建成功");
      router.push("/tickets");
    } catch {
      ElMessage.error("工单创建失败");
    } finally {
      loading.value = false;
    }
  });
};

onMounted(fetchAssets);
</script>

<template>
  <div class="create-page">
    <div class="page-header">
      <h2>创建工单</h2>
    </div>

    <el-card>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入工单标题" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入工单描述（选填）"
          />
        </el-form-item>

        <el-form-item label="资产" prop="asset_id">
          <el-select
            v-model="form.asset_id"
            placeholder="请选择资产"
            style="width: 100%"
          >
            <el-option
              v-for="asset in assets"
              :key="asset.id"
              :label="asset.name"
              :value="asset.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">
            提交工单
          </el-button>
          <el-button @click="router.push('/tickets')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: 20px;
}

h2 {
  margin: 0;
  font-size: 20px;
}

.el-card {
  max-width: 600px;
}
</style>