export interface AuthTokenResponse {
  accessToken: string;
  tokenType?: string;
}

export interface User {
  id: string;
  email: string;
  fullName: string;
  phone?: string | null;
  isAdmin: boolean;
}

export interface CurrentUserResponse {
  user: User;
  isClient?: boolean;
  isExecutor?: boolean;
  isAdmin?: boolean;
}

export interface Service {
  code: number;
  title: string;
  description?: string | null;
  departmentCode?: string | null;
  basePrice?: number | null;
  baseDurationDays?: number | null;
  requiredDocs?: Record<string, unknown> | null;
  isActive?: boolean;
}

export interface District {
  code: string;
  name: string;
  priceCoef?: number | null;
}

export interface HouseType {
  code: string;
  name: string;
  priceCoef?: number | null;
}

export interface Order {
  id: string;
  clientId: string;
  serviceCode: number;
  status: string;
  title: string;
  description?: string | null;
  address?: string | null;
  city?: string | null;
  region?: string | null;
  districtCode?: string | null;
  houseTypeCode?: string | null;
  complexity?: string | null;
  calculatorInput?: Record<string, unknown> | null;
  estimatedPrice?: number | null;
  totalPrice?: number | null;
  currentDepartmentCode?: string | null;
  aiDecisionStatus?: string | null;
  aiDecisionSummary?: string | null;
  plannedVisitAt?: string | null;
  completedAt?: string | null;
  createdAt: string;
  updatedAt?: string | null;
}

export interface OrderFile {
  id: string;
  orderId: string;
  senderId?: string | null;
  filename: string;
  path: string;
  createdAt?: string | null;
}

export interface OrderPlanVersion {
  id: string;
  orderId: string;
  versionType: string;
  plan: Record<string, unknown>;
}

export interface OrderStatusHistoryItem {
  oldStatus?: string | null;
  status: string;
  changedByUserId?: string | null;
  changedAt: string;
}

export interface ExecutorOrderListItem {
  id: string;
  status: string;
  serviceTitle: string;
  totalPrice?: number | null;
  createdAt: string;
  complexity?: string | null;
  city?: string | null;
  address?: string | null;
  departmentCode?: string | null;
}

export interface ExecutorOrderDetails {
  order?: Order;
  files?: OrderFile[];
  planOriginal?: OrderPlanVersion | null;
  planModified?: OrderPlanVersion | null;
  statusHistory?: OrderStatusHistoryItem[];
  client?: User;
  executorAssignment?: {
    executorId: string;
    status: string;
    assignedAt?: string | null;
    assignedByUserId?: string | null;
  } | null;
}

export interface ExecutorCalendarEvent {
  id: string;
  executorId: string;
  orderId?: string | null;
  title?: string | null;
  description?: string | null;
  startTime: string;
  endTime: string;
  location?: string | null;
  status?: string | null;
  createdAt?: string | null;
}
