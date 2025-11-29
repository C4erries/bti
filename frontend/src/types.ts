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
  serviceTitle?: string | null;
  address?: string | null;
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
  plan: PlanGeometry;
  comment?: string | null;
  createdById?: string | null;
  createdAt?: string | null;
}

export interface OrderStatusHistoryItem {
  oldStatus?: string | null;
  status: string;
  changedByUserId?: string | null;
  changedAt: string;
  comment?: string | null;
}

export interface ExecutorOrderListItem {
  id: string;
  status: string;
  serviceTitle: string;
  totalPrice?: number | null;
  createdAt: string;
  complexity?: string | null;
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

export interface OrderChatMessage {
  id?: string;
  orderId: string;
  senderId?: string | null;
  senderType?: string | null;
  messageText: string;
  meta?: Record<string, unknown> | null;
  createdAt?: string | null;
}

export interface ChatMessagePairResponse {
  userMessage?: OrderChatMessage;
  aiMessage?: OrderChatMessage;
}

export interface AiAnalysis {
  id: string;
  orderId: string;
  decisionStatus: string;
  summary?: string | null;
  risks?: {
    type?: string;
    description?: string;
    severity?: string | null;
    zone?: string | null;
  }[];
  legalWarnings?: string[] | null;
  financialWarnings?: string[] | null;
  recommendations?: string[] | null;
  rawResponse?: Record<string, unknown> | null;
  createdAt?: string | null;
}

export interface ClientChatThread {
  chatId: string;
  orderId?: string | null;
  serviceCode: number;
  serviceTitle: string;
  orderStatus?: string;
  lastMessageText?: string | null;
  updatedAt: string;
}

export interface SegmentGeometry {
  kind: 'segment';
  points: number[]; // [x1, y1, x2, y2]
}

export interface PolygonGeometry {
  kind: 'polygon';
  points: number[]; // [x1, y1, ..., xn, yn]
}

export type Geometry = SegmentGeometry | PolygonGeometry;

export interface WallElement {
  id: string;
  type: 'wall';
  role: 'EXISTING' | 'TO_DELETE' | 'NEW' | 'MODIFIED';
  loadBearing?: boolean | null;
  thickness?: number | null;
  geometry: SegmentGeometry;
}

export interface ZoneElement {
  id: string;
  type: 'zone';
  zoneType: string;
  relatedTo?: string[] | null;
  geometry: PolygonGeometry;
}

// Extendable for door/window/label if понадобится
export type PlanElement = WallElement | ZoneElement;

export interface PlanMeta {
  width: number;
  height: number;
  unit: 'px';
  scale: { px_per_meter: number };
  background?: any;
}

export interface PlanObject3D {
  id: string;
  type: string;
  position: { x: number; y: number; z: number };
  rotation?: { y?: number };
  size?: { x: number; y: number; z: number };
}

export interface PlanGeometry {
  meta: PlanMeta;
  elements: PlanElement[];
  objects3d?: PlanObject3D[];
}

export interface PriceBreakdown {
  baseComponent: number;
  worksComponent: number;
  featuresCoef: number;
  raw?: Record<string, unknown> | null;
}

export interface PriceEstimateResponse {
  estimatedPrice: number;
  breakdown: PriceBreakdown;
}

export interface Department {
  code: string;
  name?: string | null;
}

export interface ExecutorAnalytics {
  executorId: string;
  fullName: string;
  email: string;
  departmentCode?: string | null;
  currentLoad: number;
  lastActivity?: string | null;
  avgCompletionDays?: number | null;
  errorsRejections: number;
  totalCompleted: number;
  totalAssigned: number;
}

export interface AdminOrderListItem {
  id: string;
  status: string;
  title: string;
  description?: string | null;
  serviceCode: number;
  serviceTitle?: string | null;
  clientId: string;
  clientName?: string | null;
  executorId?: string | null;
  executorName?: string | null;
  currentDepartmentCode?: string | null;
  totalPrice?: number | null;
  filesCount: number;
  createdAt: string;
  plannedVisitAt?: string | null;
  completedAt?: string | null;
  executorComment?: string | null;
}

export interface AdminOrderDetails {
  order: Order;
  client?: User | null;
  executor?: User | null;
  executorAssignment?: {
    id: string;
    executorId: string;
    status: string;
    assignedAt?: string | null;
  } | null;
  files: OrderFile[];
  planVersions: OrderPlanVersion[];
  statusHistory: OrderStatusHistoryItem[];
}
