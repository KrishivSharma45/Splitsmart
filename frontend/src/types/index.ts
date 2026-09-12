export type TripRole = "OWNER" | "ADMIN" | "MEMBER";
export type MemberStatus = "ACTIVE" | "REMOVED";
export type TripStatus = "ACTIVE" | "ARCHIVED";
export type ExpenseCategory =
  | "FOOD"
  | "TRANSPORT"
  | "ACCOMMODATION"
  | "SHOPPING"
  | "ENTERTAINMENT"
  | "BILLS"
  | "OTHER";
export type SplitMethod = "EQUAL" | "EXACT" | "PERCENTAGE" | "SHARES";
export type ExpenseStatus = "ACTIVE" | "VOIDED";
export type SettlementStatus = "COMPLETED" | "CANCELLED";

export interface UserSummary {
  id: number;
  full_name: string;
  email: string;
}

export interface User extends UserSummary {
  is_active: boolean;
  created_at: string;
}

export interface Trip {
  id: number;
  name: string;
  description: string | null;
  destination: string | null;
  start_date: string | null;
  end_date: string | null;
  currency: string;
  status: TripStatus;
  created_by: number;
  created_at: string;
  updated_at: string;
  my_role: TripRole | null;
}

export interface TripListItem extends Trip {
  total_expenses: string;
  member_count: number;
  my_net_balance: string;
}

export interface TripMember {
  id: number;
  trip_id: number;
  role: TripRole;
  status: MemberStatus;
  joined_at: string;
  user: UserSummary;
}

export interface ExpenseSplit {
  id: number;
  user: UserSummary;
  share_amount: string;
  percentage: string | null;
  shares: number | null;
}

export interface Expense {
  id: number;
  trip_id: number;
  description: string;
  amount: string;
  currency: string;
  paid_by: UserSummary;
  category: ExpenseCategory;
  split_method: SplitMethod;
  date: string;
  notes: string | null;
  status: ExpenseStatus;
  void_reason: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
  splits: ExpenseSplit[];
  has_receipt: boolean;
}

export interface ExpenseParticipantInput {
  user_id: number;
  amount?: string;
  percentage?: string;
  shares?: number;
}

export interface Settlement {
  id: number;
  trip_id: number;
  payer: UserSummary;
  receiver: UserSummary;
  amount: string;
  currency: string;
  date: string;
  note: string | null;
  status: SettlementStatus;
  created_by: number;
  created_at: string;
}

export interface MemberBalance {
  user: UserSummary;
  total_paid: string;
  total_owed: string;
  net_balance: string;
}

export interface BalancesResponse {
  trip_id: number;
  currency: string;
  total_expenses: string;
  balances: MemberBalance[];
}

export interface DebtEdge {
  from_user: UserSummary;
  to_user: UserSummary;
  amount: string;
}

export interface DebtsResponse {
  trip_id: number;
  currency: string;
  simplified_debts: DebtEdge[];
  transaction_count: number;
}

export interface AuditLog {
  id: number;
  event_type: string;
  actor: UserSummary | null;
  trip_id: number | null;
  entity_type: string;
  entity_id: string | null;
  event_data: Record<string, unknown>;
  timestamp: string;
  previous_hash: string;
  current_hash: string;
}

export interface AuditVerifyResponse {
  status: "VALID" | "COMPROMISED";
  records_checked: number;
  broken_links: number;
  affected_record: number | null;
  affected_records: number[];
  verified_at: string;
  scope: string;
}

export interface SecurityEvent {
  id: number;
  event_type: string;
  user_id: number | null;
  ip_address: string | null;
  detail: string | null;
  created_at: string;
}

export interface SecurityOverview {
  database_status: string;
  audit_chain_status: string;
  total_audit_events: number;
  last_verification_at: string | null;
  last_verification_status: string | null;
  integrity_violations: number;
  recent_security_events: SecurityEvent[];
  recent_audit_events: AuditLog[];
  active_users_24h: number;
  failed_logins_24h: number;
}

export interface Notification {
  id: number;
  type: string;
  message: string;
  trip_id: number | null;
  entity_type: string | null;
  entity_id: number | null;
  is_read: boolean;
  created_at: string;
}

export interface CategoryBreakdownItem {
  category: string;
  total: string;
  percentage_of_total: string;
}

export interface ReportSummary {
  trip: Trip;
  total_expenses: string;
  active_expense_count: number;
  voided_expense_count: number;
  balances: MemberBalance[];
  settlements: Settlement[];
  category_breakdown: CategoryBreakdownItem[];
}

export interface DashboardSummary {
  total_spending: string;
  trip_count: number;
  active_trip_count: number;
  amount_you_owe: string;
  amount_owed_to_you: string;
  recent_expenses: Expense[];
  recent_settlements: Settlement[];
  trips: TripListItem[];
}

export interface ApiError {
  detail: string;
  errors?: unknown;
}
