<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox, type FormInstance } from "element-plus";
import { getTicket, updateTicket, approveTicket, type Ticket } from "@/api/tickets";
import { getAssets, type Asset } from "@/api/assets";
import { useUserStore } from "@/stores/user";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const ticket = ref<Ticket | null>(null);
const editing = ref(false);
const formRef = ref<FormInstance>();
const assets = ref<Asset[]>([]);

const editForm = ref({
  title: "",
  description: "",
  status: "",
  asset_id: 0
});

const statusMap: Record<string, { label: string; type: string }> = {
  draft:     { label: "草稿",   type: "info" },
  submitted: { label: "待审批", type: "warning" },
  approved:  { label: "已通过", type: "success" },
  rejected:  { label: "已拒绝", type: "danger" }
};

const statusOptions = [
  { label: "草稿",   value: "draft" },
  { label: "待审批", value: "submitted" },
  { label: "已通过", value: "approved" },
  { label: "已拒绝", value: "rejected" }
];

const fetchTicket = async () => {
  loading.value = true;
  try {
    const res = await getTicket(Number(route.params.id));
    ticket.value = res.data;
  } catch {
    ElMessage.error("获取工单详情失败");
  } finally {
    loading.value = false;
  }
};

const fetchAssets = async () => {
  const res = await getAssets();
  assets.value = res.data;
};

const startEdit = () => {
  if (!ticket.value) return;
  editForm.value = {
    title: ticket.value.title,
    description: ticket.value.description,
    status: ticket.value.status,
    asset_id: ticket.value.asset_id
  };
  editing.value = true;
};

const cancelEdit = () => {
  editing.value = false;
};

const saveEdit = async () => {
  if (!formRef.value || !ticket.value) return;
  await formRef.value.validate(async valid => {
    if (!valid) return;
    loading.value = true;
    try {
      await updateTicket(ticket.value!.id, editForm.value);
      ElMessage.success("保存成功");
      editing.value = false;
      fetchTicket();
    } catch {
      ElMessage.error("保存失败");
    } finally {
      loading.value = false;
    }
  });
};

const handleApprove = async () => {
  if (!ticket.value) return;
  await ElMessageBox.confirm(`确认通过工单「${ticket.value.title}」？`, "提示", {
    confirmButtonText: "确认",
    cancelButtonText: "取消",
    type: "warning"
  });
  try {
    await approveTicket(ticket.value.id);
    ElMessage.success("审批成功");
    fetchTicket();
  } catch {
    ElMessage.error("审批失败");
  }
};

const formatTime = (time: string) =>
  new Date(time).toLocaleString("zh-CN", { hour12: false });

onMounted(() => {
  fetchTicket();
  fetchAssets();
});
</script>

<template>
  <div v-loading="loading">
    <div class="page-header">
      <el-button link @click="router.push('/tickets')">← 返回列表</el-button>
      <h2>工单详情</h2>
      <div class="header-actions">
        <el-button v-if="!editing" @click="startEdit">编辑</el-button>
        <template v-if="editing">
          <el-button type="primary" @click="saveEdit">保存</el-button>
          <el-button @click="cancelEdit">取消</el-button>
        </template>
        <el-button
          v-if="userStore.userInfo?.is_admin && ticket?.status === 'submitted'"
          type="success"
          @click="handleApprove"
        >
          通过审批
        </el-button>
      </div>
    </div>

    <!-- 查看模式 -->
    <el-card v-if="ticket && !editing">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="工单ID">{{ ticket.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusMap[ticket.status]?.type">
            {{ statusMap[ticket.status]?.label || ticket.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{ ticket.title }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ ticket.description || "无" }}</el-descriptions-item>
        <el-descriptions-item label="资产ID">{{ ticket.asset_id }}</el-descriptions-item>
        <el-descriptions-item label="提交人ID">{{ ticket.created_by_id }}</el-descriptions-item>
        <el-descriptions-item label="审批人ID">{{ ticket.approved_by_id || "未审批" }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(ticket.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(ticket.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 编辑模式 -->
    <el-card v-if="ticket && editing">
      <el-form ref="formRef" :model="editForm" label-width="80px">
        <el-form-item label="标题" prop="title" :rules="[{ required: true, message: '请输入标题' }]">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option
              v-for="s in statusOptions"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="资产" prop="asset_id">
          <el-select v-model="editForm.asset_id" style="width: 100%">
            <el-option
              v-for="asset in assets"
              :key="asset.id"
              :label="asset.name"
              :value="asset.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
h2 {
  margin: 0;
  font-size: 20px;
  flex: 1;
}
.header-actions {
  display: flex;
  gap: 8px;
}
</style>