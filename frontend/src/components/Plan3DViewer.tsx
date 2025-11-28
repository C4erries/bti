import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import type { PlanGeometry, PlanObject3D } from '../types';
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
    scene.background = new THREE.Color(0xf5f7fb);
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
    controls.target.set(0, 0, 0);
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(5, 10, 7.5);
    scene.add(dirLight);
    scene.add(objectsGroupRef.current);

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
    const scene = sceneRef.current;
    if (!scene) return;
    const group = objectsGroupRef.current;
    while (group.children.length) group.remove(group.children[0]);

    // Ground
    const floorGeom = new THREE.PlaneGeometry(
      safeNumber(plan.meta?.width, 1000) / pxPerMeter,
      safeNumber(plan.meta?.height, 1000) / pxPerMeter,
    );
    const floorMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, side: THREE.DoubleSide });
    const floor = new THREE.Mesh(floorGeom, floorMat);
    floor.rotation.x = -Math.PI / 2;
    group.add(floor);

    buildWallsFromPlan(plan, group, pxPerMeter);
    buildZonesFromPlan(plan, group, pxPerMeter);
    buildObjects(plan, group);
  };

  const buildWallsFromPlan = (
    planData: PlanGeometry,
    group: THREE.Group,
    scale: number,
  ) => {
    const safeScale = scale > 0 ? scale : 100;
    planData.elements
      .filter((el) => el.type === 'wall' && el.geometry.kind === 'segment' && el.geometry.start && el.geometry.end)
      .forEach((wall) => {
        const { start, end } = wall.geometry;
        if (!start || !end) return;
        const dx = safeNumber(end.x) - safeNumber(start.x);
        const dy = safeNumber(end.y) - safeNumber(start.y);
        const lengthPx = Math.sqrt(dx * dx + dy * dy);
        const length = lengthPx / scale;
        if (!Number.isFinite(length)) return;
        const midX = (safeNumber(start.x) + safeNumber(end.x)) / 2;
        const midY = (safeNumber(start.y) + safeNumber(end.y)) / 2;
        const center3d = from2DTo3D(midX, midY, safeScale);
        const geo = new THREE.BoxGeometry(length, defaultHeight, wallThickness);
        const material = new THREE.MeshStandardMaterial({
          color: wall.geometry.loadBearing ? 0x475569 : 0x9ca3af,
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
    planData.elements
      .filter((el) => el.type === 'zone' && el.geometry.kind === 'polygon' && el.geometry.points?.length)
      .forEach((zone) => {
        const pts = (zone.geometry.points || []).filter(
          (p) => Number.isFinite(p.x) && Number.isFinite(p.y),
        );
        if (pts.length < 3) return;
        const shape = new THREE.Shape();
        pts.forEach((p, idx) => {
          const mapped = from2DTo3D(p.x, p.y, safeScale);
          if (idx === 0) shape.moveTo(mapped.x, mapped.z);
          else shape.lineTo(mapped.x, mapped.z);
        });
        const geometry = new THREE.ShapeGeometry(shape);
        geometry.rotateX(-Math.PI / 2);
        const material = new THREE.MeshStandardMaterial({
          color: zone.geometry.zoneType ? 0xcbd5e1 : 0xe2e8f0,
          opacity: 0.8,
          transparent: true,
          side: THREE.DoubleSide,
        });
        const mesh = new THREE.Mesh(geometry, material);
        group.add(mesh);
      });
  };

  const buildObjects = (planData: PlanGeometry, group: THREE.Group) => {
    (planData.objects3d || []).forEach((obj) => {
      const size = obj.size || { x: 1, y: 1, z: 1 };
      const geometry = new THREE.BoxGeometry(size.x, size.y, size.z);
      const color = getColorForType(obj.type);
      const material = new THREE.MeshStandardMaterial({ color });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(obj.position.x, obj.position.y ?? size.y / 2, obj.position.z);
      if (obj.rotation?.y) mesh.rotation.y = obj.rotation.y;
      (mesh as any).userData.planObjectId = obj.id;
      group.add(mesh);
    });
  };

  const getColorForType = (type: string) => {
    switch (type) {
      case 'sofa':
        return 0x38bdf8;
      case 'table':
        return 0x22c55e;
      case 'wardrobe':
        return 0xf59e0b;
      case 'bed':
        return 0xa855f7;
      default:
        return 0x94a3b8;
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
