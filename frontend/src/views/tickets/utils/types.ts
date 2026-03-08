export interface TicketItem {
  id: number;
  title: string;
  status: "pending" | "approved" | "rejected";
  description: string;
  creator: string;
  create_time: string;
  priority: number;
}

export interface FormProps {
  formInline: TicketItem;
}