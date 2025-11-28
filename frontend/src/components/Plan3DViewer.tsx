import { Canvas, useThree, type ThreeEvent } from '@react-three/fiber';
import { Grid, OrbitControls, Stats, TransformControls } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { Box3, DoubleSide, Group, Mesh, Shape, Vector3 } from 'three';
import type { OrbitControls as OrbitControlsImpl, TransformControls as TransformControlsImpl } from 'three-stdlib';
import type { PlanGeometry, PlanObject3D } from '../types';
import {
  buildWallSegments,
  buildZonePolygons,
  from2DTo3D,
  getPxPerMeter,
  safeNumber,
} from '../utils/plan3d';
import type { ZonePolygon3D } from '../utils/plan3d';
import { buttonClass, cardClass, inputClass, subtleButtonClass } from './ui';

export interface Plan3DViewerProps {
  plan: PlanGeometry;
  onPlanChange: (plan: PlanGeometry) => void;
}

const WALL_HEIGHT = 2.7;
const DEFAULT_OBJECT_SIZE = { x: 2, y: 0.8, z: 1 };

const zoneColorByType = (zoneType?: string) => {
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
  <group>
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
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

const Walls = ({ plan }: { plan: PlanGeometry }) => {
  const walls = useMemo(() => buildWallSegments(plan), [plan]);
  return (
    <group>
      {walls.map((wall) => (
        <mesh
          key={wall.id}
          position={[wall.center.x, WALL_HEIGHT / 2, wall.center.z]}
          rotation={[0, wall.angle, 0]}
          castShadow
          receiveShadow
        >
          <boxGeometry args={[wall.length, WALL_HEIGHT, wall.thickness]} />
          <meshStandardMaterial color={wall.loadBearing ? '#475569' : '#9ca3af'} />
        </mesh>
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

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.001, 0]} receiveShadow>
      <shapeGeometry args={[shape]} />
      <meshStandardMaterial
        color={zoneColorByType(zone.zoneType)}
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

  const size = obj.size || DEFAULT_OBJECT_SIZE;
  const position = obj.position || { x: 0, y: size.y / 2, z: 0 };
  const rotationY = obj.rotation?.y || 0;
  const color = selected ? '#2563eb' : '#94a3b8';

  const handleTransformChange = useCallback(() => {
    if (!meshRef.current) return;
    const { position: pos, rotation } = meshRef.current;
    onObjectChange({
      ...obj,
      position: { x: pos.x, y: pos.y, z: pos.z },
      rotation: { ...obj.rotation, y: rotation.y },
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
    <group ref={groupRef}>
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
  const [newType, setNewType] = useState('sofa');
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
              ...obj.rotation,
              y: (obj.rotation?.y || 0) + (direction === 'left' ? -Math.PI / 2 : Math.PI / 2),
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
              onChange={(e) => setNewType(e.target.value)}
            >
              <option value="sofa">Sofa</option>
              <option value="table">Table</option>
              <option value="wardrobe">Wardrobe</option>
              <option value="bed">Bed</option>
              <option value="chair">Chair</option>
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
