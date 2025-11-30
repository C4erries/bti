import { Canvas, useThree, type ThreeEvent } from '@react-three/fiber';
import { Grid, OrbitControls, Stats, TransformControls } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { Box3, DoubleSide, Group, Mesh, Shape, Texture, TextureLoader, Vector3 } from 'three';
import type { OrbitControls as OrbitControlsImpl, TransformControls as TransformControlsImpl } from 'three-stdlib';
import type { PlanGeometry, PlanObject3D } from '../types';
import {
  buildWallSegments,
  buildZonePolygons,
  from2DTo3D,
  getPxPerMeter,
  safeNumber,
} from '../utils/plan3d';
import type { ZonePolygon3D, WallSegment3D } from '../utils/plan3d';
import { buttonClass, cardClass, inputClass, subtleButtonClass } from './ui';

export interface Plan3DViewerProps {
  plan: PlanGeometry;
  onPlanChange: (plan: PlanGeometry) => void;
}

const DEFAULT_WALL_HEIGHT = 2.7;
const DEFAULT_OBJECT_SIZE = { x: 2, y: 0.8, z: 1 };

const useOptionalTexture = (textureUrl?: string | null) => {
  const [texture, setTexture] = useState<Texture | null>(null);

  useEffect(() => {
    let active = true;
    if (!textureUrl) {
      setTexture(null);
      return;
    }
    const loader = new TextureLoader();
    loader.load(
      textureUrl,
      (loaded) => {
        if (active) setTexture(loaded);
      },
      undefined,
      () => {
        if (active) setTexture(null);
      },
    );
    return () => {
      active = false;
    };
  }, [textureUrl]);

  return texture;
};

const zoneColorByType = (zoneType?: string, styleColor?: string | null) => {
  if (styleColor) return styleColor;
  switch (zoneType) {
    case 'kitchen':
      return '#f59e0b';
    case 'bathroom':
      return '#38bdf8';
    case 'living_room':
      return '#34d399';
    case 'bedroom':
      return '#a855f7';
    default:
      return '#e2e8f0';
  }
};

const Ground = ({ width, height }: { width: number; height: number }) => (
  <group position={[width / 2, 0, height / 2]}>
    <mesh rotation={[Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[width, height]} />
      <meshStandardMaterial color="#f9fafb" />
    </mesh>
    <Grid
      args={[width, height]}
      cellSize={1}
      cellColor="#cbd5e1"
      sectionColor="#94a3b8"
      sectionThickness={0.08}
      infiniteGrid={false}
      position={[0, 0.001, 0]}
    />
  </group>
);

const WallMesh = ({ wall, height }: { wall: WallSegment3D; height: number }) => {
  const texture = useOptionalTexture(wall.style?.textureUrl ?? null);
  const color = wall.style?.color ?? (wall.loadBearing ? '#475569' : '#9ca3af');

  return (
    <mesh
      position={[wall.center.x, height / 2, wall.center.z]}
      rotation={[0, wall.angle, 0]}
      castShadow
      receiveShadow
    >
      <boxGeometry args={[wall.length, height, wall.thickness]} />
      <meshStandardMaterial color={color} map={texture ?? undefined} />
    </mesh>
  );
};

const Walls = ({ plan }: { plan: PlanGeometry }) => {
  const walls = useMemo(() => buildWallSegments(plan), [plan]);
  const wallHeight = plan.meta?.ceiling_height_m ?? DEFAULT_WALL_HEIGHT;
  return (
    <group>
      {walls.map((wall) => (
        <WallMesh key={wall.id} wall={wall} height={wallHeight} />
      ))}
    </group>
  );
};

const ZoneMesh = ({ zone }: { zone: ZonePolygon3D }) => {
  const shape = useMemo(() => {
    const s = new Shape();
    zone.points.forEach((pt, idx) => {
      if (idx === 0) s.moveTo(pt.x, pt.z);
      else s.lineTo(pt.x, pt.z);
    });
    return s;
  }, [zone]);
  const texture = useOptionalTexture(zone.style?.textureUrl ?? null);
  const color = zoneColorByType(zone.zoneType, zone.style?.color ?? null);

  return (
    <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0.001, 0]} receiveShadow>
      <shapeGeometry args={[shape]} />
      <meshStandardMaterial
        color={color}
        map={texture ?? undefined}
        transparent
        opacity={0.75}
        side={DoubleSide}
      />
    </mesh>
  );
};

const Zones = ({ plan }: { plan: PlanGeometry }) => {
  const zones = useMemo(() => buildZonePolygons(plan), [plan]);

  return (
    <group>
      {zones.map((zone) => (
        <ZoneMesh key={zone.id} zone={zone} />
      ))}
    </group>
  );
};

interface PlanObjectMeshProps {
  obj: PlanObject3D;
  selected: boolean;
  controlsMode: 'translate' | 'rotate';
  onSelect: (id: string | null) => void;
  onObjectChange: (obj: PlanObject3D) => void;
}

const PlanObjectMesh = ({
  obj,
  selected,
  controlsMode,
  onSelect,
  onObjectChange,
}: PlanObjectMeshProps) => {
  const meshRef = useRef<Mesh>(null);
  const transformRef = useRef<TransformControlsImpl>(null);
  const orbitControls = useThree((state) => state.controls) as OrbitControlsImpl | null;

  const size = obj.size ?? DEFAULT_OBJECT_SIZE;
  const position = obj.position ?? { x: 0, y: size.y / 2, z: 0 };
  const rotationY = obj.rotation?.y ?? 0;
  const color = selected ? '#2563eb' : '#94a3b8';

  const handleTransformChange = useCallback(() => {
    if (!meshRef.current) return;
    const { position: pos, rotation } = meshRef.current;
    onObjectChange({
      ...obj,
      position: { x: pos.x, y: pos.y, z: pos.z },
      rotation: { ...(obj.rotation ?? {}), y: rotation.y },
    });
  }, [obj, onObjectChange]);

  useEffect(() => {
    const transform = transformRef.current;
    const orbit = orbitControls;
    if (!transform || !orbit) return;
    const toggle = (event: { value: boolean }) => {
      orbit.enabled = !event.value;
    };
    transform.addEventListener('dragging-changed' as any, toggle as any);
    return () => transform.removeEventListener('dragging-changed' as any, toggle as any);
  }, [orbitControls]);

  const meshNode = (
    <mesh
      ref={meshRef}
      position={[position.x, position.y ?? size.y / 2, position.z]}
      rotation={[0, rotationY, 0]}
      onClick={(e: ThreeEvent<MouseEvent>) => {
        e.stopPropagation();
        onSelect(obj.id);
      }}
      castShadow
      receiveShadow
    >
      <boxGeometry
        args={[
          size.x || DEFAULT_OBJECT_SIZE.x,
          size.y || DEFAULT_OBJECT_SIZE.y,
          size.z || DEFAULT_OBJECT_SIZE.z,
        ]}
      />
      <meshStandardMaterial color={color} opacity={0.95} transparent />
    </mesh>
  );

  if (!selected) return meshNode;

  const showX = controlsMode === 'translate';
  const showZ = controlsMode === 'translate';
  const showY = controlsMode === 'rotate';

  return (
    <TransformControls
      ref={transformRef}
      mode={controlsMode}
      showX={showX}
      showY={showY}
      showZ={showZ}
      onObjectChange={handleTransformChange}
    >
      {meshNode}
    </TransformControls>
  );
};

interface SceneContentProps {
  plan: PlanGeometry;
  selectedId: string | null;
  controlsMode: 'translate' | 'rotate';
  onSelect: (id: string | null) => void;
  onObjectChange: (obj: PlanObject3D) => void;
}

const SceneContent = ({
  plan,
  selectedId,
  controlsMode,
  onSelect,
  onObjectChange,
}: SceneContentProps) => {
  const groupRef = useRef<Group>(null);
  const { camera } = useThree();
  const controls = useThree((state) => state.controls) as OrbitControlsImpl | null;
  const pxPerMeter = getPxPerMeter(plan);
  const width = safeNumber(plan.meta?.width, 1000) / pxPerMeter;
  const height = safeNumber(plan.meta?.height, 1000) / pxPerMeter;
  const objects = plan.objects3d || [];
  
  // Вычисляем центр плана для центрирования сцены
  const sceneCenter = useMemo(() => {
    const walls = buildWallSegments(plan);
    const zones = buildZonePolygons(plan);
    
    // Собираем все точки для вычисления bounding box
    const allPoints: { x: number; z: number }[] = [];
    
    // Точки из стен
    walls.forEach(wall => {
      allPoints.push(wall.p1, wall.p2);
    });
    
    // Точки из зон
    zones.forEach(zone => {
      allPoints.push(...zone.points);
    });
    
    // Точки из 3D объектов (если они уже в метрах)
    objects.forEach(obj => {
      if (obj.position) {
        allPoints.push({ x: obj.position.x, z: obj.position.z });
      }
    });
    
    // Добавляем углы плана для правильного центрирования
    const planCenter2D = from2DTo3D(
      safeNumber(plan.meta?.width, 0) / 2,
      safeNumber(plan.meta?.height, 0) / 2,
      pxPerMeter
    );
    allPoints.push(planCenter2D);
    
    // Добавляем углы плана
    const corners = [
      from2DTo3D(0, 0, pxPerMeter),
      from2DTo3D(safeNumber(plan.meta?.width, 0), 0, pxPerMeter),
      from2DTo3D(0, safeNumber(plan.meta?.height, 0), pxPerMeter),
      from2DTo3D(safeNumber(plan.meta?.width, 0), safeNumber(plan.meta?.height, 0), pxPerMeter),
    ];
    allPoints.push(...corners);
    
    // Вычисляем bounding box
    let minX = Infinity, maxX = -Infinity;
    let minZ = Infinity, maxZ = -Infinity;
    
    allPoints.forEach(pt => {
      minX = Math.min(minX, pt.x);
      maxX = Math.max(maxX, pt.x);
      minZ = Math.min(minZ, pt.z);
      maxZ = Math.max(maxZ, pt.z);
    });
    
    // Если нет точек, используем размеры плана
    if (allPoints.length === 0 || !isFinite(minX)) {
      const planCenter2D = from2DTo3D(
        safeNumber(plan.meta?.width, 0) / 2,
        safeNumber(plan.meta?.height, 0) / 2,
        pxPerMeter
      );
      return { x: planCenter2D.x, z: planCenter2D.z };
    }
    
    // Центр bounding box
    return {
      x: (minX + maxX) / 2,
      z: (minZ + maxZ) / 2,
    };
  }, [plan, width, height, objects, pxPerMeter]);
  
  const fitKey = useMemo(
    () => JSON.stringify({ w: plan.meta?.width, h: plan.meta?.height, el: (plan.elements || []).map((e) => e.id) }),
    [plan.meta?.height, plan.meta?.width, plan.elements],
  );

  useEffect(() => {
    const group = groupRef.current;
    if (!group) return;
    const box = new Box3().setFromObject(group);
    if (box.isEmpty()) return;
    const center = new Vector3();
    const size = new Vector3();
    box.getCenter(center);
    box.getSize(size);
    const maxDim = Math.max(size.x, size.z, size.y);
    const distance = Math.max(maxDim * 1.5, 4);
    camera.position.set(center.x + distance, Math.max(distance, size.y + 2), center.z + distance);
    camera.near = 0.1;
    camera.far = Math.max(distance * 8, 30);
    camera.lookAt(center);
    camera.updateProjectionMatrix();
    if (controls) {
      controls.target.copy(center);
      controls.update();
    }
    // Fit is tied to plan layout (meta + elements). Objects movement/addition should not jerk the camera.
  }, [camera, controls, fitKey]);

  return (
    <group ref={groupRef} position={[-sceneCenter.x, 0, -sceneCenter.z]}>
      <Ground width={width} height={height} />
      <Walls plan={plan} />
      <Zones plan={plan} />
      <group>
        {objects.map((obj) => (
          <PlanObjectMesh
            key={obj.id}
            obj={obj}
            selected={selectedId === obj.id}
            controlsMode={controlsMode}
            onSelect={onSelect}
            onObjectChange={onObjectChange}
          />
        ))}
      </group>
    </group>
  );
};

const Plan3DViewer = ({ plan, onPlanChange }: Plan3DViewerProps) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [controlsMode, setControlsMode] = useState<'translate' | 'rotate'>('translate');
  const [newType, setNewType] = useState<PlanObject3D['type']>('chair');
  const pxPerMeter = getPxPerMeter(plan);

  const addObject = () => {
    const center = from2DTo3D(
      safeNumber(plan.meta?.width, 0) / 2,
      safeNumber(plan.meta?.height, 0) / 2,
      pxPerMeter,
    );
    const size = DEFAULT_OBJECT_SIZE;
    const newObj: PlanObject3D = {
      id: crypto.randomUUID(),
      type: newType,
      position: { x: center.x, y: size.y / 2, z: center.z },
      size,
      rotation: { y: 0 },
    };
    const objects = plan.objects3d || [];
    onPlanChange({ ...plan, objects3d: [...objects, newObj] });
    setSelectedId(newObj.id);
  };

  const updateObject = (updated: PlanObject3D) => {
    const objects = plan.objects3d || [];
    const next = objects.map((obj) => (obj.id === updated.id ? updated : obj));
    onPlanChange({ ...plan, objects3d: next });
  };

  const rotateSelected = (direction: 'left' | 'right') => {
    if (!selectedId) return;
    const objects = plan.objects3d || [];
    const updated = objects.map((obj) =>
      obj.id === selectedId
        ? {
            ...obj,
            rotation: {
              ...(obj.rotation ?? {}),
              y: (obj.rotation?.y ?? 0) + (direction === 'left' ? -Math.PI / 2 : Math.PI / 2),
            },
          }
        : obj,
    );
    onPlanChange({ ...plan, objects3d: updated });
  };

  return (
    <div className="space-y-3">
      <div className={cardClass}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-slate-700">План (3D)</p>
            <p className="text-xs text-slate-500">
              Можно вращать камеру, выбирать объект и перемещать его по XZ или вращать вокруг Y.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              className={inputClass}
              value={controlsMode}
              onChange={(e) => setControlsMode(e.target.value as 'translate' | 'rotate')}
            >
              <option value="translate">Перемещение</option>
              <option value="rotate">Поворот</option>
            </select>
            <select
              className={inputClass}
              value={newType}
              onChange={(e) => setNewType(e.target.value as PlanObject3D['type'])}
            >
              <option value="chair">Стул</option>
              <option value="table">Стол</option>
              <option value="bed">Кровать</option>
              <option value="window">Окно</option>
              <option value="door">Дверь</option>
            </select>
            <button className={buttonClass} onClick={addObject}>
              Добавить
            </button>
            {selectedId && (
              <>
                <button className={subtleButtonClass} onClick={() => rotateSelected('left')}>
                  ↺
                </button>
                <button className={subtleButtonClass} onClick={() => rotateSelected('right')}>
                  ↻
                </button>
                <button className={subtleButtonClass} onClick={() => setSelectedId(null)}>
                  Снять выбор
                </button>
              </>
            )}
          </div>
        </div>
      </div>
      <div className="h-[600px] w-full overflow-hidden rounded-xl border border-slate-200 bg-white">
        <Canvas
          camera={{ position: [5, 6, 5], fov: 60, near: 0.1, far: 200 }}
          shadows
          onPointerMissed={() => setSelectedId(null)}
        >
          <color attach="background" args={['#e5e7eb']} />
          <ambientLight intensity={0.8} />
          <directionalLight position={[5, 10, 7]} intensity={0.6} />
          <OrbitControls makeDefault />
          <SceneContent
            plan={plan}
            selectedId={selectedId}
            controlsMode={controlsMode}
            onSelect={setSelectedId}
            onObjectChange={updateObject}
          />
          <Stats showPanel={0} className="hidden md:block" />
        </Canvas>
      </div>
    </div>
  );
};

export default Plan3DViewer;
