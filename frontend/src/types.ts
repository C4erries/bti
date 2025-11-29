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
  status: string;
  title: string;
  description?: string | null;
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

export interface PlanScale {
  px_per_meter: number;
}

export interface PlanBackground {
  file_id: string;
  opacity: number; // 0..1
}

export interface ElementStyle {
  color?: string;
  textureUrl?: string | null;
}

export interface PlanMeta {
  width: number;
  height: number;
  unit: 'px';
  scale?: PlanScale | null;
  background?: PlanBackground | null;
  ceiling_height_m?: number; // 1.8..5
}

export interface WallOpening {
  id: string;
  type: 'door' | 'window' | 'arch' | 'custom';
  from_m: number;
  to_m: number;
  bottom_m: number;
  top_m: number;
}

export interface WallGeometry {
  kind: 'segment';
  points: number[]; // length 4
  openings?: WallOpening[];
}

export interface PolygonGeometry {
  kind: 'polygon';
  points: number[]; // length >= 6
}

export interface PointGeometry {
  kind: 'point';
  x: number;
  y: number;
}

export type Geometry = WallGeometry | PolygonGeometry | PointGeometry;

export interface PlanElementBase {
  id: string;
  type: string; // 'wall' | 'zone' | 'label' | ...
  role?: 'EXISTING' | 'TO_DELETE' | 'NEW' | 'MODIFIED';
  loadBearing?: boolean | null;
  thickness?: number | null;
  zoneType?: string;
  relatedTo?: string[] | null;
  selected?: boolean;
  style?: ElementStyle | null;
  geometry: Geometry;
  // Extra props are allowed by schema (e.g., label text)
  [key: string]: unknown;
}

export interface WallElement extends PlanElementBase {
  type: 'wall';
  geometry: WallGeometry;
}

export interface ZoneElement extends PlanElementBase {
  type: 'zone';
  geometry: PolygonGeometry;
}

export type PlanElement = PlanElementBase;

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

export interface Rotation3 {
  x?: number;
  y?: number;
  z?: number;
}

export interface PlanObject3D {
  id: string;
  type: 'chair' | 'table' | 'bed' | 'window' | 'door';
  position: Vec3;
  size?: Vec3 | null;
  rotation?: Rotation3 | null;
  wallId?: string | null;
  zoneId?: string | null;
  selected?: boolean;
  meta?: Record<string, unknown> | null;
}

export interface PlanGeometry {
  meta: PlanMeta;
  elements: PlanElement[];
  objects3d?: PlanObject3D[];
}

export interface OrderPlanVersion {
  id: string;
  orderId: string;
  versionType: 'ORIGINAL' | 'MODIFIED';
  plan: PlanGeometry;
  comment?: string | null;
  createdById?: string | null;
  createdAt: string; // ISO date-time
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
  title: string;
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
  orderStatus?: string;
  lastMessageText?: string | null;
  updatedAt: string;
}

export interface CalculatorWorks {
  walls?: boolean;
  wet_zone?: boolean;
  doorways?: boolean;
}

export interface CalculatorFeatures {
  basement?: boolean;
  join_apartments?: boolean;
}

export interface CalculatorInput {
  area?: number;
  works?: CalculatorWorks;
  features?: CalculatorFeatures;
  urgent?: boolean;
  notes?: string;
}

export interface PriceCalculatorRequest {
  districtCode?: string | null;
  houseTypeCode?: string | null;
  calculatorInput?: CalculatorInput | null;
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
