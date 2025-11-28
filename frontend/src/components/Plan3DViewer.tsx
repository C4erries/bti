import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import type { PlanGeometry, PlanObject3D, WallElement, ZoneElement } from '../types';
import { buttonClass, cardClass, inputClass, subtleButtonClass } from './ui';

export interface Plan3DViewerProps {
  plan: PlanGeometry;
  onPlanChange: (plan: PlanGeometry) => void;
}

const defaultHeight = 2.7;
const wallThickness = 0.2;

const safeNumber = (val: any, fallback = 0) =>
  Number.isFinite(Number(val)) ? Number(val) : fallback;

const from2DTo3D = (xPx: number, yPx: number, pxPerMeter: number) => {
  const scale = pxPerMeter > 0 ? pxPerMeter : 100;
  return {
    x: safeNumber(xPx, 0) / scale,
    z: -safeNumber(yPx, 0) / scale,
  };
};

const Plan3DViewer = ({ plan, onPlanChange }: Plan3DViewerProps) => {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const objectsGroupRef = useRef<THREE.Group>(new THREE.Group());
  const raycaster = useRef(new THREE.Raycaster());
  const mouse = useRef(new THREE.Vector2());
  const selectedIdRef = useRef<string | null>(null);
  const draggingRef = useRef(false);
  const planRef = useRef<PlanGeometry>(plan);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [newType, setNewType] = useState('sofa');

  useEffect(() => {
    planRef.current = plan;
  }, [plan]);

  // Init scene
  useEffect(() => {
    if (!mountRef.current) return;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xe5e7eb);
    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight || 600;
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(5, 6, 5);
    camera.lookAt(0, 0, 0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mountRef.current.appendChild(renderer.domElement);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.enablePan = true;
    controls.enableZoom = true;
    controls.enableRotate = true;
    controls.minDistance = 1;
    controls.maxDistance = 200;
    controls.target.set(0, 0, 0);
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(5, 10, 7.5);
    scene.add(dirLight);
    const grid = new THREE.GridHelper(50, 50);
    scene.add(grid);
    scene.add(objectsGroupRef.current);
    const axes = new THREE.AxesHelper(5);
    scene.add(axes);

    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
      const w = mountRef.current?.clientWidth || width;
      const h = mountRef.current?.clientHeight || height;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', handleResize);

    rendererRef.current = renderer;
    sceneRef.current = scene;
    cameraRef.current = camera;
    controlsRef.current = controls;

    const onPointerMove = (event: PointerEvent) => handlePointerMove(event);
    const onPointerDown = (event: PointerEvent) => handlePointerDown(event);
    const onPointerUp = () => handlePointerUp();
    renderer.domElement.addEventListener('pointermove', onPointerMove);
    renderer.domElement.addEventListener('pointerdown', onPointerDown);
    renderer.domElement.addEventListener('pointerup', onPointerUp);

    return () => {
      window.removeEventListener('resize', handleResize);
      renderer.domElement.removeEventListener('pointermove', onPointerMove);
      renderer.domElement.removeEventListener('pointerdown', onPointerDown);
      renderer.domElement.removeEventListener('pointerup', onPointerUp);
      renderer.dispose();
      controls.dispose();
    };
  }, []);

  // Rebuild scene on plan change
  useEffect(() => {
    rebuildScene();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan]);

  const pxPerMeter = plan.meta?.scale?.px_per_meter || 100;

  const handlePointerDown = (event: PointerEvent) => {
    if (!rendererRef.current || !cameraRef.current) return;
    const { left, top, width, height } = rendererRef.current.domElement.getBoundingClientRect();
    mouse.current.x = ((event.clientX - left) / width) * 2 - 1;
    mouse.current.y = -((event.clientY - top) / height) * 2 + 1;
    raycaster.current.setFromCamera(mouse.current, cameraRef.current);
    const intersects = raycaster.current.intersectObjects(objectsGroupRef.current.children, true);
    const hit = intersects.find((i) => (i.object as any).userData.planObjectId);
    if (hit) {
      const id = (hit.object as any).userData.planObjectId as string;
      selectedIdRef.current = id;
      setSelectedId(id);
      draggingRef.current = true;
    }
  };

  const handlePointerMove = (event: PointerEvent) => {
    if (!draggingRef.current || !rendererRef.current || !cameraRef.current) return;
    const { left, top, width, height } = rendererRef.current.domElement.getBoundingClientRect();
    mouse.current.x = ((event.clientX - left) / width) * 2 - 1;
    mouse.current.y = -((event.clientY - top) / height) * 2 + 1;
    raycaster.current.setFromCamera(mouse.current, cameraRef.current);
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    const point = new THREE.Vector3();
    raycaster.current.ray.intersectPlane(plane, point);
    if (selectedIdRef.current) {
      const mesh = objectsGroupRef.current.children.find(
        (c) => (c as any).userData.planObjectId === selectedIdRef.current,
      ) as THREE.Mesh | undefined;
      if (mesh) {
        mesh.position.x = point.x;
        mesh.position.z = point.z;
        updateObjectPosition(selectedIdRef.current, mesh.position);
      }
    }
  };

  const handlePointerUp = () => {
    draggingRef.current = false;
    selectedIdRef.current = null;
  };

  const updateObjectPosition = (id: string, position: THREE.Vector3) => {
    const updatedObjects = (planRef.current.objects3d || []).map((obj) =>
      obj.id === id
        ? { ...obj, position: { x: position.x, y: position.y, z: position.z } }
        : obj,
    );
    onPlanChange({ ...planRef.current, objects3d: updatedObjects });
  };

  const rebuildScene = () => {
    if (!sceneRef.current) return;
    console.log(
      'Plan3DViewer: elements',
      plan.elements.length,
      'objects3d',
      plan.objects3d?.length ?? 0,
    );
    const group = objectsGroupRef.current;
    while (group.children.length) group.remove(group.children[0]);

    // Ground
    const floorGeom = new THREE.PlaneGeometry(
      safeNumber(plan.meta?.width, 1000) / pxPerMeter,
      safeNumber(plan.meta?.height, 1000) / pxPerMeter,
    );
    const floorMat = new THREE.MeshStandardMaterial({ color: 0xf9fafb, side: THREE.DoubleSide });
    const floor = new THREE.Mesh(floorGeom, floorMat);
    floor.rotation.x = -Math.PI / 2;
    group.add(floor);

    buildWallsFromPlan(plan, group, pxPerMeter);
    buildZonesFromPlan(plan, group, pxPerMeter);
    buildObjects(plan, group);

    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (camera && controls && group.children.length > 0) {
      const box = new THREE.Box3().setFromObject(group);
      const size = new THREE.Vector3();
      const center = new THREE.Vector3();
      box.getSize(size);
      box.getCenter(center);
      // сдвигаем группу в центр, чтобы объект был около (0,0,0)
      group.position.sub(center);
      const recalcBox = new THREE.Box3().setFromObject(group);
      const recalcCenter = new THREE.Vector3();
      const recalcSize = new THREE.Vector3();
      recalcBox.getCenter(recalcCenter);
      recalcBox.getSize(recalcSize);
      const maxDim = Math.max(recalcSize.x, recalcSize.y, recalcSize.z) || 1;
      const distance = Math.max(maxDim * 1.2, 10);
      controls.target.copy(recalcCenter);
      camera.position.set(recalcCenter.x + distance, recalcCenter.y + distance, recalcCenter.z + distance);
      camera.lookAt(center);
      camera.near = 0.01;
      camera.far = distance * 10;
      camera.updateProjectionMatrix();
      controls.update();
      console.log('Bounding box', { size: recalcSize, center: recalcCenter, distance });
    }

    console.log(
      '3D objects in group:',
      group.children.length,
      group.children.map((c, idx) => ({
        idx,
        id: (c as any).userData?.planObjectId,
        pos: { x: c.position.x, y: c.position.y, z: c.position.z },
      })),
    );
  };

  const buildWallsFromPlan = (
    planData: PlanGeometry,
    group: THREE.Group,
    scale: number,
  ) => {
    const safeScale = scale > 0 ? scale : 100;
    const walls = planData.elements.filter(
      (el) =>
        el.type === 'wall' &&
        (el as any).geometry?.kind === 'segment' &&
        Array.isArray((el as any).geometry?.points) &&
        (el as any).geometry.points.length >= 4,
    );
    console.log('Walls found:', walls.length);
    walls.forEach((el) => {
      const wall = el as WallElement;
      const pts = wall.geometry.points as number[];
      const [x1, y1, x2, y2] = pts;
      const dx = safeNumber(x2) - safeNumber(x1);
      const dy = safeNumber(y2) - safeNumber(y1);
      const lengthPx = Math.sqrt(dx * dx + dy * dy);
      const length = lengthPx / safeScale;
      if (!Number.isFinite(length)) return;
      const midX = (safeNumber(x1) + safeNumber(x2)) / 2;
      const midY = (safeNumber(y1) + safeNumber(y2)) / 2;
      const center3d = from2DTo3D(midX, midY, safeScale);
      const thicknessMeters =
        wall.thickness != null
          ? safeNumber(wall.thickness, wallThickness * safeScale) / safeScale
          : wallThickness;
      const geo = new THREE.BoxGeometry(length, defaultHeight, thicknessMeters);
      const isLoadBearing = !!wall.loadBearing;
      const material = new THREE.MeshStandardMaterial({
        color: isLoadBearing ? 0x4b5563 : 0x9ca3af,
      });
      const mesh = new THREE.Mesh(geo, material);
      mesh.position.set(center3d.x, defaultHeight / 2, center3d.z);
      mesh.rotation.y = -Math.atan2(dy, dx);
      group.add(mesh);
    });
  };

  const buildZonesFromPlan = (
    planData: PlanGeometry,
    group: THREE.Group,
    scale: number,
  ) => {
    const safeScale = scale > 0 ? scale : 100;
    const zones = planData.elements.filter(
      (el) =>
        el.type === 'zone' &&
        (el as any).geometry?.kind === 'polygon' &&
        Array.isArray((el as any).geometry?.points) &&
        (el as any).geometry.points.length >= 6,
    );
    console.log('Zones found:', zones.length);
    zones.forEach((el) => {
      const zone = el as ZoneElement;
      const raw = zone.geometry.points as number[];
      const pts: { x: number; y: number }[] = [];
      for (let i = 0; i + 1 < raw.length; i += 2) {
        pts.push({ x: safeNumber(raw[i]), y: safeNumber(raw[i + 1]) });
      }
      if (pts.length < 3) return;
      const shape = new THREE.Shape();
      pts.forEach((p, idx) => {
        const mapped = from2DTo3D(p.x, p.y, safeScale);
        if (idx === 0) shape.moveTo(mapped.x, mapped.z);
        else shape.lineTo(mapped.x, mapped.z);
      });
      const geometry = new THREE.ShapeGeometry(shape);
      geometry.rotateX(-Math.PI / 2);
      const zoneType = zone.zoneType;
      const material = new THREE.MeshStandardMaterial({
        color: zoneType ? 0x22c55e : 0xe2e8f0,
        opacity: 0.8,
        transparent: true,
        side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geometry, material);
      group.add(mesh);
    });
  };

  const buildObjects = (planData: PlanGeometry, group: THREE.Group) => {
    const palette = [0xff3b30, 0x22c55e, 0x3b82f6, 0xf59e0b, 0xa855f7];
    (planData.objects3d || []).forEach((obj, idx) => {
      const geometry = new THREE.BoxGeometry(2, 2, 2);
      const material = new THREE.MeshStandardMaterial({
        color: palette[idx % palette.length],
      });
      const mesh = new THREE.Mesh(geometry, material);
      const x = safeNumber(obj.position?.x, 0);
      const z = safeNumber(obj.position?.z, 0);
      const yRaw = safeNumber(obj.position?.y, 1);
      const y = yRaw === 0 ? 1 : yRaw;
      mesh.position.set(x, y, z);
      (mesh as any).userData.planObjectId = obj.id || `obj_${idx}`;
      group.add(mesh);
    });
    // Добавляем пару фиктивных кубов для отладки, чтобы всегда видеть несколько объектов
    for (let i = 0; i < 3; i++) {
      const geometry = new THREE.BoxGeometry(2, 2, 2);
      const material = new THREE.MeshStandardMaterial({
        color: palette[(planData.objects3d?.length || 0 + i) % palette.length],
        opacity: 0.6,
        transparent: true,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(i * 3, 1, -i * 3);
      (mesh as any).userData.planObjectId = `debug_${i}`;
      group.add(mesh);
    }
  };

  const addObject = () => {
    const defaults: PlanObject3D = {
      id: crypto.randomUUID(),
      type: newType,
      position: { x: 0, y: 0.5, z: 0 },
      size: { x: 1.2, y: 0.7, z: 0.8 },
      rotation: { y: 0 },
    };
    const updatedObjects = [...(plan.objects3d || []), defaults];
    onPlanChange({ ...plan, objects3d: updatedObjects });
    setSelectedId(defaults.id);
  };

  const rotateObject = (dir: 'left' | 'right') => {
    if (!selectedIdRef.current && !selectedId) return;
    const id = selectedIdRef.current || selectedId!;
    const objects = plan.objects3d || [];
    const updated = objects.map((obj) =>
      obj.id === id
        ? {
            ...obj,
            rotation: { y: (obj.rotation?.y || 0) + (dir === 'left' ? -Math.PI / 2 : Math.PI / 2) },
          }
        : obj,
    );
    onPlanChange({ ...plan, objects3d: updated });
  };

  return (
    <div className="space-y-3">
      <div className={cardClass}>
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <p className="text-sm text-slate-600">План (3D)</p>
            <p className="text-xs text-slate-500">Потяните объект, чтобы переместить по XZ.</p>
          </div>
          <div className="flex items-center gap-2">
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
                <button className={subtleButtonClass} onClick={() => rotateObject('left')}>
                  ⟲
                </button>
                <button className={subtleButtonClass} onClick={() => rotateObject('right')}>
                  ⟳
                </button>
              </>
            )}
          </div>
        </div>
      </div>
      <div ref={mountRef} className="h-[600px] w-full overflow-hidden rounded-xl border border-slate-200 bg-white" />
    </div>
  );
};

export default Plan3DViewer;
