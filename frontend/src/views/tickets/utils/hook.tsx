import { message } from "@/utils/message";
import { getTicketList, approveTicket } from "@/api/v1/tickets";
import { type PaginationProps } from "@pureadmin/table";
import { reactive, ref, onMounted, h } from "vue";

export function useTicket() {
  const dataList = ref([]);
  const loading = ref(true);
  const pagination = reactive<PaginationProps>({
    total: 0,
    pageSize: 10,
    currentPage: 1,
    background: true
  });

  async function onSearch() {
    loading.value = true;
    const { data } = await getTicketList(); // 对接 GET /api/v1/tickets
    dataList.value = data.list;
    pagination.total = data.total;
    loading.value = false;
  }

  async function handleApprove(row) {
    await approveTicket(row.id); // 对接 POST /api/v1/tickets/{id}/approve
    message(`工单 ${row.title} 审批成功`, { type: "success" });
    onSearch();
  }

  onMounted(() => {
    onSearch();
  });

  return { loading, dataList, pagination, onSearch, handleApprove };
}