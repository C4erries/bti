import type {
  ElementStyle,
  PlanGeometry,
  PlanObject3D,
  WallElement,
  ZoneElement,
} from '../types';

export const safeNumber = (value: unknown, fallback = 0) => {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
};

export const getPxPerMeter = (plan?: PlanGeometry) => {
  const scale = plan?.meta?.scale;
  return scale && scale.px_per_meter > 0 ? scale.px_per_meter : 100;
};

export const from2DTo3D = (xPx: number, yPx: number, pxPerMeter: number) => {
  const scale = pxPerMeter > 0 ? pxPerMeter : 100;
  return {
    x: safeNumber(xPx, 0) / scale,
    z: safeNumber(yPx, 0) / scale,
  };
};

export interface WallSegment3D {
  id: string;
  p1: { x: number; z: number };
  p2: { x: number; z: number };
  center: { x: number; z: number };
  length: number;
  thickness: number;
  loadBearing: boolean;
  role: WallElement['role'];
  angle: number;
  style?: ElementStyle | null;
}

export const buildWallSegments = (plan: PlanGeometry): WallSegment3D[] => {
  const pxPerMeter = getPxPerMeter(plan);
  return (plan.elements || [])
    .filter(
      (el): el is WallElement =>
        el.type === 'wall' &&
        el.geometry?.kind === 'segment' &&
        Array.isArray(el.geometry?.points) &&
        el.geometry.points.length >= 4,
    )
    .map((wall) => {
      const [x1, y1, x2, y2] = wall.geometry.points;
      const p1 = from2DTo3D(x1, y1, pxPerMeter);
      const p2 = from2DTo3D(x2, y2, pxPerMeter);
      const center = { x: (p1.x + p2.x) / 2, z: (p1.z + p2.z) / 2 };
      const dx = p2.x - p1.x;
      const dz = p2.z - p1.z;
      const length = Math.hypot(dx, dz);
      const angle = Math.atan2(dz, dx);
      const thickness =
        wall.thickness != null
          ? safeNumber(wall.thickness, 0) / pxPerMeter
          : 0.2;
      return {
        id: wall.id,
        p1,
        p2,
        center,
        length: length > 0 ? length : 0,
        thickness: thickness > 0 ? thickness : 0.2,
        loadBearing: !!wall.loadBearing,
        role: wall.role,
        angle,
        style: wall.style,
      };
    })
    .filter((wall) => wall.length > 0.0001);
};

export interface ZonePolygon3D {
  id: string;
  zoneType?: string;
  points: { x: number; z: number }[];
  style?: ElementStyle | null;
}

export const buildZonePolygons = (plan: PlanGeometry): ZonePolygon3D[] => {
  const pxPerMeter = getPxPerMeter(plan);
  return (plan.elements || [])
    .filter(
      (el): el is ZoneElement =>
        el.type === 'zone' &&
        el.geometry?.kind === 'polygon' &&
        Array.isArray(el.geometry?.points) &&
        el.geometry.points.length >= 6,
    )
    .map((zone) => {
      const raw = zone.geometry.points;
      const points: { x: number; z: number }[] = [];
      for (let i = 0; i + 1 < raw.length; i += 2) {
        const x = raw[i];
        const y = raw[i + 1];
        points.push(from2DTo3D(x, y, pxPerMeter));
      }
      return { id: zone.id, zoneType: zone.zoneType, points, style: zone.style };
    })
    .filter((zone) => zone.points.length >= 3);
};

export const withUpdatedObject = (
  plan: PlanGeometry,
  updated: PlanObject3D,
): PlanGeometry => {
  const objects = plan.objects3d || [];
  const next = objects.some((o) => o.id === updated.id)
    ? objects.map((o) => (o.id === updated.id ? updated : o))
    : [...objects, updated];
  return { ...plan, objects3d: next };
};
