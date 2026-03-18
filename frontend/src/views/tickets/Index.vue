<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";       // 消息提示 & 确认弹窗
import { getTickets, approveTicket } from "@/api/tickets";
import type { Ticket } from "@/types/ticket"; 
import { TICKET_STATUS_MAP } from "@/types/ticket";           // 状态码 → 中文的映射表
import { useUserStore } from "@/stores/user";
import { formatTime } from "@/utils/format";                  // 时间格式化工具
import StatusTag from "@/components/StatusTag.vue";           // 状态标签组件

const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);                                   // 控制表格加载动画
const tickets = ref<Ticket[]>([]);                            // 当前页的工单数据
const total = ref(0);                                         // 总条数（用于分页器）
const currentPage = ref(1);                                    // 当前页码
const pageSize = ref(10);                                       // 每页显示条数

const fetchTickets = async () => {
  loading.value = true;
  try {
    // 根据页码计算偏移量，例如第2页、每页10条 → skip=10
    const skip = (currentPage.value - 1) * pageSize.value;
    const res = await getTickets({ skip, limit: pageSize.value });
    tickets.value = res.data;
    // 后端没有返回总数，用返回条数是否"不足一页"来估算 total
    // 不足一页 → 说明已经是最后一页了，total 就是当前实际总数
    // 满一页   → 说明后面可能还有，total 多加 1 让分页器显示"下一页"按钮
    total.value = res.data.length < pageSize.value
      ? skip + res.data.length
      : skip + res.data.length + 1;
  } catch {
    ElMessage.error("获取工单列表失败");
  } finally {
    loading.value = false;    // 无论成功失败都关闭加载动画
  }
};

// 切换页码时重新拉取数据
const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchTickets();
};

// 切换每页条数时，重置到第一页再拉取
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  fetchTickets();
};

const handleApprove = async (row: Ticket) => {
  // 先弹出确认框，防止误操作
  await ElMessageBox.confirm(`确认通过工单「${row.title}」？`, "提示", {
    confirmButtonText: "确认", cancelButtonText: "取消", type: "warning"
  });
  try {
    await approveTicket(row.id);
    ElMessage.success("审批成功");
    fetchTickets();
  } catch {
    ElMessage.error("审批失败");
  }
};

// 页面挂载时自动拉取第一页数据
onMounted(fetchTickets);
</script>

<template>
  <div>
    <!-- 页头：标题 + 创建按钮 -->
    <div class="page-header">
      <h2>工单列表</h2>
      <el-button type="primary" @click="router.push('/tickets/create')">+ 创建工单</el-button>
    </div>

    <!-- 工单表格，loading 时显示加载动画 -->
    <el-table :data="tickets" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" sortable />
      <el-table-column prop="title" label="标题" min-width="150" />
      <!-- show-overflow-tooltip：内容过长时悬浮显示完整文本 -->
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

      <!-- 状态列：用 StatusTag 组件渲染带颜色的状态标签 -->
      <el-table-column prop="status" label="状态" width="100" sortable>
        <template #default="{ row }">
          <StatusTag :status="row.status" :status-map="TICKET_STATUS_MAP" />
        </template>
      </el-table-column>

      <el-table-column prop="created_by_id" label="提交人" width="100" sortable />

      <!-- 时间列：用 formatTime 工具函数格式化时间戳 -->
      <el-table-column prop="created_at" label="创建时间" width="180" sortable>
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>

      <!-- 操作列：固定在右侧不随横向滚动消失 -->
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="router.push(`/tickets/${row.id}`)">查看</el-button>
          <!-- 审批按钮：仅管理员可见，且工单状态必须是 submitted -->
          <el-button
            v-if="userStore.userInfo?.is_admin && row.status === 'submitted'"
            link type="success"
            @click="handleApprove(row)"
          >审批</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页器：右对齐，支持切换页码和每页条数 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50]"
        :total="total"
        layout="total, sizes, prev, pager, next"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<style scoped>
/*
 * scoped 表示这里的样式只作用于当前组件，不会影响其他页面
 * 即使别的组件也有 .pagination 这个类名，也不会互相干扰
 */
.pagination {
  margin-top: 20px;        /* 和上方表格保持 20px 间距 */
  display: flex;           /* 开启 flex 布局 */
  justify-content: flex-end; /* 让分页器靠右对齐 */
}
</style>