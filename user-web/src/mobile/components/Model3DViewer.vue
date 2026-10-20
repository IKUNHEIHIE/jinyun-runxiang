<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

const props = defineProps<{
  url: string;
  autoRotate?: boolean;
  wireframe?: boolean;
  label?: string;
}>();
const emit = defineEmits<{
  loaded: [stats: { triangles: number; meshes: number; materials: number }];
  progress: [value: number];
  fps: [value: number];
  error: [message: string];
}>();

const host = ref<HTMLDivElement>();
let renderer: THREE.WebGLRenderer | undefined;
let scene: THREE.Scene | undefined;
let camera: THREE.PerspectiveCamera | undefined;
let controls: OrbitControls | undefined;
let group: THREE.Group | undefined;
let envTarget: THREE.WebGLRenderTarget | undefined;
let resizeObserver: ResizeObserver | undefined;
let loadToken = 0;
let currentUrl = "";
let disposed = false;

function disposeModel() {
  if (!group || !scene) return;
  scene.remove(group);
  group.traverse((node) => {
    const mesh = node as THREE.Mesh;
    if (!mesh.isMesh) return;
    mesh.geometry?.dispose();
    const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    materials.forEach((material) => {
      Object.values(material).forEach((value) => {
        if (value && (value as THREE.Texture).isTexture) (value as THREE.Texture).dispose();
      });
      material.dispose();
    });
  });
  group = undefined;
}

async function loadModel(url: string) {
  if (!scene || !url) return;
  const token = ++loadToken;
  currentUrl = url;
  const loader = new GLTFLoader();
  try {
    const gltf = await loader.loadAsync(url, (event) => {
      if (event.total) emit("progress", Math.round((event.loaded / event.total) * 100));
    });
    if (token !== loadToken || disposed) {
      gltf.scene.traverse((node) => {
        const mesh = node as THREE.Mesh;
        if (mesh.isMesh) {
          mesh.geometry?.dispose();
          const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
          materials.forEach((material) => material.dispose());
        }
      });
      return;
    }
    disposeModel();
    const root = gltf.scene;
    let triangles = 0;
    let meshes = 0;
    const materialSet = new Set<THREE.Material>();
    root.traverse((node) => {
      const mesh = node as THREE.Mesh;
      if (!mesh.isMesh) return;
      // DragonAttenuation ships with a checkered studio backdrop; keep the sculpture only.
      if (/cloth|backdrop|checker/i.test(mesh.name)) {
        mesh.visible = false;
        return;
      }
      meshes += 1;
      const geometry = mesh.geometry;
      triangles += Math.round(
        (geometry.index ? geometry.index.count : geometry.attributes.position.count) / 3,
      );
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      materials.forEach((material) => {
        const standard = material as THREE.MeshStandardMaterial;
        if (standard.map) standard.map.colorSpace = THREE.SRGBColorSpace;
        standard.wireframe = !!props.wireframe;
        standard.needsUpdate = true;
        materialSet.add(material);
      });
    });
    // Invisible helper meshes (studio cloth, backdrop) must not distort the fit.
    root.updateMatrixWorld(true);
    const box = new THREE.Box3();
    root.traverse((node) => {
      const mesh = node as THREE.Mesh;
      if (!mesh.isMesh || !mesh.visible) return;
      mesh.geometry.computeBoundingBox();
      const bounds = mesh.geometry.boundingBox?.clone().applyMatrix4(mesh.matrixWorld);
      if (bounds) box.union(bounds);
    });
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    root.position.sub(center);
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    group = new THREE.Group();
    group.add(root);
    group.scale.setScalar(2.2 / maxDim);
    group.position.y = 0.02;
    scene.add(group);
    emit("loaded", { triangles, meshes, materials: materialSet.size });
    emit("progress", 100);
  } catch {
    if (token === loadToken) emit("error", "三维模型加载失败，请检查网络后重试");
  }
}

function buildStage() {
  if (!scene) return;
  const platform = new THREE.Mesh(
    new THREE.CircleGeometry(1.36, 96),
    new THREE.MeshStandardMaterial({
      color: 0x1c1712,
      metalness: 0.68,
      roughness: 0.34,
      transparent: true,
      opacity: 0.94,
    }),
  );
  platform.rotation.x = -Math.PI / 2;
  platform.position.y = -1.13;
  scene.add(platform);

  const goldRing = new THREE.Mesh(
    new THREE.RingGeometry(1.37, 1.4, 128),
    new THREE.MeshBasicMaterial({ color: 0xc9a84c, transparent: true, opacity: 0.72 }),
  );
  goldRing.rotation.x = -Math.PI / 2;
  goldRing.position.y = -1.125;
  scene.add(goldRing);

  const cyanRing = new THREE.Mesh(
    new THREE.RingGeometry(1.52, 1.535, 128),
    new THREE.MeshBasicMaterial({ color: 0x8b1a1a, transparent: true, opacity: 0.34 }),
  );
  cyanRing.rotation.x = -Math.PI / 2;
  cyanRing.position.y = -1.125;
  scene.add(cyanRing);

  const grid = new THREE.GridHelper(5, 20, 0x7a5c2e, 0x2b241b);
  const gridMaterial = grid.material as THREE.Material;
  gridMaterial.transparent = true;
  gridMaterial.opacity = 0.26;
  grid.position.y = -1.14;
  scene.add(grid);
}

function setup() {
  const element = host.value;
  if (!element) return;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  } catch {
    emit("error", "当前设备不支持 WebGL 三维渲染");
    return;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(element.clientWidth, element.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.02;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  element.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(38, element.clientWidth / element.clientHeight, 0.1, 100);
  camera.position.set(2.45, 1.35, 3.1);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.enablePan = false;
  controls.minDistance = 2.2;
  controls.maxDistance = 6;
  controls.minPolarAngle = Math.PI * 0.18;
  controls.maxPolarAngle = Math.PI * 0.52;
  controls.autoRotate = props.autoRotate !== false;
  controls.autoRotateSpeed = 0.85;
  controls.target.set(0, 0, 0);

  const pmrem = new THREE.PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  envTarget = pmrem.fromScene(room, 0.04);
  scene.environment = envTarget.texture;
  scene.environmentIntensity = 0.5;
  room.dispose?.();
  pmrem.dispose();

  scene.add(new THREE.AmbientLight(0xfff4e2, 0.5));
  scene.add(new THREE.HemisphereLight(0xfff7ea, 0x4a2f18, 0.55));
  const key = new THREE.DirectionalLight(0xffe9c4, 2.2);
  key.position.set(4.2, 6, 4);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xd4a34a, 1.1);
  rim.position.set(-4.5, 2.4, -3.6);
  scene.add(rim);
  const gold = new THREE.PointLight(0xe0a33a, 7, 9, 2);
  gold.position.set(0, -0.6, 2.3);
  scene.add(gold);

  buildStage();
  loadModel(props.url);

  resizeObserver = new ResizeObserver(() => {
    if (!renderer || !camera || !element.clientWidth || !element.clientHeight) return;
    camera.aspect = element.clientWidth / element.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(element.clientWidth, element.clientHeight);
  });
  resizeObserver.observe(element);

  let frames = 0;
  let lastFpsAt = performance.now();
  renderer.setAnimationLoop(() => {
    controls?.update();
    if (renderer && scene && camera) renderer.render(scene, camera);
    const now = performance.now();
    frames += 1;
    if (now - lastFpsAt >= 1000) {
      emit("fps", Math.round((frames * 1000) / (now - lastFpsAt)));
      frames = 0;
      lastFpsAt = now;
    }
  });
}

watch(
  () => props.url,
  (url) => {
    if (url && url !== currentUrl) loadModel(url);
  },
);
watch(
  () => props.autoRotate,
  (value) => {
    if (controls) controls.autoRotate = value !== false;
  },
);
watch(
  () => props.wireframe,
  (value) => {
    group?.traverse((node) => {
      const mesh = node as THREE.Mesh;
      if (!mesh.isMesh) return;
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      materials.forEach((material) => {
        (material as THREE.MeshStandardMaterial).wireframe = !!value;
      });
    });
  },
);

function resetView() {
  camera?.position.set(2.45, 1.35, 3.1);
  controls?.target.set(0, 0, 0);
  controls?.update();
}

/** Keyboard orbit for players without a pointer; mirrors what dragging does. */
function orbit(deltaAzimuth: number, deltaPolar: number) {
  if (!camera || !controls) return;
  const offset = camera.position.clone().sub(controls.target);
  const spherical = new THREE.Spherical().setFromVector3(offset);
  spherical.theta += deltaAzimuth;
  spherical.phi = Math.min(Math.max(spherical.phi + deltaPolar, 0.05), Math.PI - 0.05);
  offset.setFromSpherical(spherical);
  camera.position.copy(controls.target).add(offset);
  camera.lookAt(controls.target);
  controls.update();
}

function onKeydown(event: KeyboardEvent) {
  const step = event.shiftKey ? 0.5 : 0.18;
  const keys: Record<string, [number, number]> = {
    ArrowLeft: [step, 0],
    ArrowRight: [-step, 0],
    ArrowUp: [0, -step * 0.7],
    ArrowDown: [0, step * 0.7],
  };
  const move = keys[event.key];
  if (!move) return;
  event.preventDefault();
  orbit(move[0], move[1]);
}

defineExpose({ resetView });

onMounted(setup);
onBeforeUnmount(() => {
  disposed = true;
  loadToken += 1;
  resizeObserver?.disconnect();
  renderer?.setAnimationLoop(null);
  controls?.dispose();
  disposeModel();
  envTarget?.dispose();
  if (renderer) {
    renderer.dispose();
    renderer.domElement.remove();
  }
});
</script>

<template>
  <div
    ref="host"
    class="model-viewer"
    role="img"
    tabindex="0"
    :aria-label="props.label || '三维模型实时预览，聚焦后可用方向键旋转视角'"
    @keydown="onKeydown"
  />
</template>

<style scoped>
.model-viewer {
  position: absolute;
  inset: 0;
  touch-action: none;
}
.model-viewer :deep(canvas) {
  display: block;
  width: 100%;
  height: 100%;
}
.model-viewer:focus-visible {
  outline: 2px solid rgba(201, 168, 76, 0.75);
  outline-offset: -2px;
}
</style>
