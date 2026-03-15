<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getAssets } from "@/api/assets";
import type { Asset } from "@/types/asset";
import { formatTime } from "@/utils/format";

const router = useRouter();
const loading = ref(false);
const assets = ref<Asset[]>([]);

const fetchAssets = async () => {
  loading.value = true;
  try {
    const res = await getAssets();
    assets.value = res.data;
  } catch {
    ElMessage.error("获取资产列表失败");
  } finally {
    loading.value = false;
  }
};

onMounted(fetchAssets);
</script>

<template>
  <div>
    <div class="page-header">
      <h2>资产列表</h2>
      <el-button type="primary" @click="router.push('/assets/create')">+ 创建资产</el-button>
    </div>
    <el-table :data="assets" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" sortable />
      <el-table-column prop="name" label="名称" min-width="150" sortable />
      <el-table-column prop="asset_type" label="类型" width="120" sortable />
      <el-table-column prop="serial_number" label="序列号" width="150" sortable />
      <el-table-column prop="location" label="位置" width="150" sortable />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180" sortable>
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/assets/${row.id}`)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>