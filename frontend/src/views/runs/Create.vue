<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { createRun } from "@/api/runs";
import { getTickets, type Ticket } from "@/api/tickets";

const router = useRouter();
const formRef = ref<FormInstance>();
const loading = ref(false);
const tickets = ref<Ticket[]>([]);

const form = ref({
  run_type: "proof",
  script_id: "",
  ticket_id: undefined as number | undefined,
  execution_context: {}
});

const rules: FormRules = {
  script_id: [{ required: true, message: "请输入脚本ID", trigger: "blur" }],
  ticket_id: [{ required: true, message: "请选择工单", trigger: "change" }]
};

const runTypeOptions = [
  { label: "Proof", value: "proof" },
  { label: "Action", value: "action" }
];

const fetchTickets = async () => {
  const res = await getTickets();
  tickets.value = res.data.filter(t => t.status === "approved");
};

const onSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async valid => {
    if (!valid) return;
    loading.value = true;
    try {
      await createRun(form.value as any);
      ElMessage.success("运行创建成功");
      router.push("/runs");
    } catch {
      ElMessage.error("运行创建失败");
    } finally {
      loading.value = false;
    }
  });
};

onMounted(fetchTickets);
</script>

<template>
  <div>
    <div class="page-header">
      <h2>创建运行</h2>
    </div>

    <el-card>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="运行类型" prop="run_type">
          <el-select v-model="form.run_type" style="width: 100%">
            <el-option v-for="t in runTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="脚本ID" prop="script_id">
          <el-input v-model="form.script_id" placeholder="请输入脚本ID" />
        </el-form-item>
        <el-form-item label="关联工单" prop="ticket_id">
          <el-select v-model="form.ticket_id" placeholder="选择已审批的工单" style="width: 100%">
            <el-option
              v-for="t in tickets"
              :key="t.id"
              :label="`#${t.id} ${t.title}`"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">创建运行</el-button>
          <el-button @click="router.push('/runs')">取消</el-button>
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