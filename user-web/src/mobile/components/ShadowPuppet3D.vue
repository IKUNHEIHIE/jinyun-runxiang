<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import * as THREE from "three";

const props = defineProps<{ step: number }>();
const host = ref<HTMLDivElement | null>(null);
const IMAGE_URL = "/design/images/15cbc40b47a025f417fc5a7b16263fe9.webp";

let renderer: THREE.WebGLRenderer | undefined;
let camera: THREE.PerspectiveCamera | undefined;
let frame = 0;
let observer: ResizeObserver | undefined;
const disposables: Array<{ dispose: () => void }> = [];
const materials: Record<string, THREE.ShaderMaterial> = {};
const dynamic: {
  head?: THREE.Mesh;
  left?: THREE.Mesh;
  right?: THREE.Mesh;
  joints?: THREE.Group;
  rods?: THREE.Group;
  sheet?: THREE.Mesh;
} = {};
let state = { sheet: 1, line: 0, silhouette: 0, engrave: 0, colors: 0, joints: 0, rods: 0, spread: 0 };

const vertexShader = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;

const fragmentShader = `
uniform sampler2D map;
uniform float mode;
uniform float opacity;
uniform vec2 texel;
varying vec2 vUv;
float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
void main() {
  vec4 source = texture2D(map, vUv);
  float l = luma(source.rgb);
  float sat = max(source.r, max(source.g, source.b)) - min(source.r, min(source.g, source.b));
  if (mode < 0.5) {
    float a = smoothstep(0.035, 0.15, l);
    if (a < 0.02) discard;
    gl_FragColor = vec4(source.rgb * 1.05, a * opacity);
    return;
  }
  if (mode < 1.5) {
    float a = smoothstep(0.035, 0.13, l);
    if (a < 0.02) discard;
    if (l > 0.72 && sat < 0.14) {
      gl_FragColor = vec4(0.96, 0.90, 0.78, 0.92 * opacity);
    } else {
      gl_FragColor = vec4(0.08, 0.06, 0.045, opacity);
    }
    return;
  }
  float tl = luma(texture2D(map, vUv + vec2(-texel.x, texel.y)).rgb);
  float tr = luma(texture2D(map, vUv + vec2(texel.x, texel.y)).rgb);
  float bl = luma(texture2D(map, vUv + vec2(-texel.x, -texel.y)).rgb);
  float br = luma(texture2D(map, vUv + vec2(texel.x, -texel.y)).rgb);
  float edge = abs(l - tl) + abs(l - tr) + abs(l - bl) + abs(l - br);
  float a = smoothstep(0.15, 0.5, edge);
  if (a < 0.02) discard;
  vec3 ink = mode < 2.5 ? vec3(0.16, 0.11, 0.075) : vec3(0.96, 0.90, 0.78);
  float strength = mode < 2.5 ? 0.92 : 0.55;
  gl_FragColor = vec4(ink, a * strength * opacity);
}`;

function shader(texture: THREE.Texture, mode: number) {
  const material = new THREE.ShaderMaterial({
    uniforms: {
      map: { value: texture },
      mode: { value: mode },
      opacity: { value: 1 },
      texel: { value: new THREE.Vector2(1 / (texture.image?.width || 512), 1 / (texture.image?.height || 512)) },
    },
    vertexShader,
    fragmentShader,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  disposables.push(material);
  return material;
}

function loadImage(): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("皮影图样加载失败"));
    image.src = IMAGE_URL;
  });
}

function cropTexture(image: HTMLImageElement, u0: number, v0: number, u1: number, v1: number) {
  const sx = Math.round(image.naturalWidth * u0);
  const sy = Math.round(image.naturalHeight * v0);
  const sw = Math.round(image.naturalWidth * (u1 - u0));
  const sh = Math.round(image.naturalHeight * (v1 - v0));
  const canvas = document.createElement("canvas");
  canvas.width = sw;
  canvas.height = sh;
  canvas.getContext("2d")!.drawImage(image, sx, sy, sw, sh, 0, 0, sw, sh);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  return texture;
}

function hideTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 420;
  canvas.height = 860;
  const ctx = canvas.getContext("2d")!;
  const gradient = ctx.createLinearGradient(0, 0, 420, 860);
  gradient.addColorStop(0, "#eed8ae");
  gradient.addColorStop(0.55, "#e3c38f");
  gradient.addColorStop(1, "#d2ac73");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 420, 860);
  ctx.globalAlpha = 0.16;
  ctx.strokeStyle = "#8a6536";
  for (let i = 0; i < 46; i += 1) {
    const y = 18 + Math.random() * 820;
    ctx.beginPath();
    ctx.moveTo(12, y);
    ctx.bezierCurveTo(120, y - 14, 280, y + 18, 408, y - 6);
    ctx.lineWidth = 0.7 + Math.random() * 1.2;
    ctx.stroke();
  }
  ctx.globalAlpha = 0.35;
  ctx.strokeStyle = "#b8862f";
  ctx.setLineDash([12, 8]);
  ctx.lineWidth = 2;
  ctx.strokeRect(14, 14, 392, 832);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function screenTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d")!;
  const gradient = ctx.createRadialGradient(256, 240, 24, 256, 260, 330);
  gradient.addColorStop(0, "#f9e9c6");
  gradient.addColorStop(0.52, "#e7c18a");
  gradient.addColorStop(1, "#7a5330");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 512, 512);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function plainPlane(texture: THREE.Texture, width: number, height: number, opacity = 0) {
  const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, height), material);
  disposables.push(material);
  return mesh;
}

function pin(x: number, y: number) {
  const material = new THREE.MeshBasicMaterial({ color: 0xd9b56a, transparent: true });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(0.024, 12, 12), material);
  mesh.position.set(x, y, 0.14);
  disposables.push(material);
  return mesh;
}

function rod(from: THREE.Vector3, to: THREE.Vector3) {
  const direction = new THREE.Vector3().subVectors(to, from);
  const material = new THREE.MeshBasicMaterial({ color: 0xb08a4c, transparent: true, opacity: 0 });
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, direction.length(), 6), material);
  mesh.position.copy(from).add(to).multiplyScalar(0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize());
  disposables.push(material);
  return mesh;
}

function targets(step: number) {
  if (step <= 0) return { sheet: 1, line: 0, silhouette: 0, engrave: 0, colors: 0, joints: 0, rods: 0, spread: 0 };
  if (step === 1) return { sheet: 0.72, line: 1, silhouette: 0, engrave: 0, colors: 0, joints: 0, rods: 0, spread: 0 };
  if (step === 2) return { sheet: 0.16, line: 0, silhouette: 1, engrave: 0.55, colors: 0, joints: 0, rods: 0, spread: 0 };
  if (step === 3) return { sheet: 0, line: 0, silhouette: 0, engrave: 0, colors: 1, joints: 0, rods: 0, spread: 0.04 };
  if (step === 4) return { sheet: 0, line: 0, silhouette: 0, engrave: 0, colors: 1, joints: 1, rods: 0, spread: 0 };
  return { sheet: 0, line: 0, silhouette: 0, engrave: 0, colors: 1, joints: 1, rods: 1, spread: 0 };
}

async function setup() {
  if (!host.value) return;
  const scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(36, 1, 0.1, 20);
  camera.position.set(0.12, 0.02, 4.1);
  camera.lookAt(0, 0.02, 0);
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x000000, 0);
  host.value.appendChild(renderer.domElement);
  disposables.push(renderer);

  const screenMaterial = new THREE.MeshBasicMaterial({ map: screenTexture() });
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 2.6), screenMaterial);
  screen.position.z = -0.35;
  scene.add(screen);
  disposables.push(screenMaterial);

  const group = new THREE.Group();
  group.position.y = 0.08;
  scene.add(group);

  const image = await loadImage();
  const fullTexture = new THREE.Texture(image);
  fullTexture.colorSpace = THREE.SRGBColorSpace;
  fullTexture.anisotropy = 8;
  fullTexture.needsUpdate = true;

  const fullWidth = 1.61;
  const fullHeight = 2.15;
  const full = new THREE.Mesh(new THREE.PlaneGeometry(fullWidth, fullHeight), shader(fullTexture, 1));
  full.renderOrder = 2;
  group.add(full);
  materials.silhouette = full.material as THREE.ShaderMaterial;

  const engrave = new THREE.Mesh(new THREE.PlaneGeometry(fullWidth, fullHeight), shader(fullTexture, 3));
  engrave.position.z = 0.012;
  engrave.renderOrder = 3;
  group.add(engrave);
  materials.engrave = engrave.material as THREE.ShaderMaterial;

  const line = new THREE.Mesh(new THREE.PlaneGeometry(fullWidth, fullHeight), shader(fullTexture, 2));
  line.position.z = 0.066;
  line.renderOrder = 4;
  group.add(line);
  materials.line = line.material as THREE.ShaderMaterial;

  const crops = [
    { key: "body", u0: 0.28, v0: 0.27, u1: 0.78, v1: 1.0, z: 0 },
    { key: "head", u0: 0.30, v0: 0.0, u1: 0.72, v1: 0.31, z: 0.03 },
    { key: "left", u0: 0.05, v0: 0.25, u1: 0.44, v1: 0.56, z: 0.05 },
    { key: "right", u0: 0.48, v0: 0.26, u1: 0.87, v1: 0.6, z: 0.04 },
  ];
  for (const crop of crops) {
    const texture = cropTexture(image, crop.u0, crop.v0, crop.u1, crop.v1);
    const width = fullWidth * (crop.u1 - crop.u0);
    const height = fullHeight * (crop.v1 - crop.v0);
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, height), shader(texture, 0));
    mesh.position.set(
      -fullWidth / 2 + fullWidth * ((crop.u0 + crop.u1) / 2),
      fullHeight / 2 - fullHeight * ((crop.v0 + crop.v1) / 2),
      crop.z,
    );
    mesh.renderOrder = 6;
    mesh.userData.base = mesh.position.clone();
    group.add(mesh);
    materials[crop.key] = mesh.material as THREE.ShaderMaterial;
    if (crop.key === "head") dynamic.head = mesh;
    if (crop.key === "left") dynamic.left = mesh;
    if (crop.key === "right") dynamic.right = mesh;
  }

  const sheet = plainPlane(hideTexture(), 1.42, 2.5, 0.85);
  sheet.position.z = 0.12;
  sheet.renderOrder = 9;
  group.add(sheet);
  dynamic.sheet = sheet;

  const joints = new THREE.Group();
  joints.add(pin(0.0, 0.62), pin(0.02, 0.18), pin(-0.34, 0.42), pin(0.36, 0.4));
  joints.children.forEach((child) => {
    child.scale.setScalar(0.001);
    (child as THREE.Mesh).renderOrder = 10;
  });
  group.add(joints);
  dynamic.joints = joints;

  const rods = new THREE.Group();
  rods.add(
    rod(new THREE.Vector3(0, 0.6, 0.1), new THREE.Vector3(-0.92, -1.3, 0.18)),
    rod(new THREE.Vector3(0.02, 0.18, 0.1), new THREE.Vector3(-1.0, -1.34, 0.18)),
    rod(new THREE.Vector3(0.36, 0.4, 0.1), new THREE.Vector3(0.86, -1.28, 0.18)),
  );
  rods.children.forEach((child) => ((child as THREE.Mesh).renderOrder = 8));
  group.add(rods);
  dynamic.rods = rods;

  state = targets(props.step);
  const resize = () => {
    if (!host.value || !renderer || !camera) return;
    const { clientWidth, clientHeight } = host.value;
    if (!clientWidth || !clientHeight) return;
    renderer.setSize(clientWidth, clientHeight, false);
    camera.aspect = clientWidth / clientHeight;
    camera.updateProjectionMatrix();
  };
  observer = new ResizeObserver(resize);
  observer.observe(host.value);
  resize();

  const clock = new THREE.Clock();
  const animate = () => {
    frame = requestAnimationFrame(animate);
    if (!renderer || !camera) return;
    const t = clock.getElapsedTime();
    const next = targets(props.step);
    for (const key of Object.keys(next) as Array<keyof typeof next>) {
      state[key] += (next[key] - state[key]) * 0.09;
    }
    materials.line.uniforms.opacity.value = state.line;
    materials.silhouette.uniforms.opacity.value = state.silhouette;
    materials.engrave.uniforms.opacity.value = state.engrave;
    (dynamic.sheet!.material as THREE.MeshBasicMaterial).opacity = 0.85 * state.sheet;
    for (const key of ["head", "left", "right", "body"] as const) {
      materials[key].uniforms.opacity.value = state.colors;
    }
    const spread = state.spread;
    if (dynamic.head && dynamic.left && dynamic.right) {
      const headBase = dynamic.head.userData.base as THREE.Vector3;
      const leftBase = dynamic.left.userData.base as THREE.Vector3;
      const rightBase = dynamic.right.userData.base as THREE.Vector3;
      dynamic.head.position.x += (headBase.x + 0.1 * spread - dynamic.head.position.x) * 0.1;
      dynamic.head.position.y += (headBase.y + 0.16 * spread - dynamic.head.position.y) * 0.1;
      dynamic.head.position.z += (headBase.z + 0.12 * spread - dynamic.head.position.z) * 0.1;
      dynamic.left.position.x += (leftBase.x - 0.16 * spread - dynamic.left.position.x) * 0.1;
      dynamic.left.position.y += (leftBase.y + 0.04 * spread - dynamic.left.position.y) * 0.1;
      dynamic.left.position.z += (leftBase.z + 0.1 * spread - dynamic.left.position.z) * 0.1;
      dynamic.right.position.x += (rightBase.x + 0.14 * spread - dynamic.right.position.x) * 0.1;
      dynamic.right.position.y += (rightBase.y - 0.02 * spread - dynamic.right.position.y) * 0.1;
      dynamic.right.position.z += (rightBase.z + 0.08 * spread - dynamic.right.position.z) * 0.1;
    }
    dynamic.joints?.children.forEach((child) => child.scale.setScalar(Math.max(0.001, state.joints)));
    dynamic.rods?.children.forEach((child) => {
      ((child as THREE.Mesh).material as THREE.MeshBasicMaterial).opacity = state.rods;
    });
    group.rotation.y = Math.sin(t * 0.42) * 0.035 + (props.step >= 5 ? Math.sin(t * 0.34) * 0.2 : 0);
    group.rotation.z = Math.sin(t * 0.31) * 0.01;
    renderer.render(scene, camera);
  };
  animate();
}

onMounted(setup);
onBeforeUnmount(() => {
  cancelAnimationFrame(frame);
  observer?.disconnect();
  disposables.forEach((item) => item.dispose());
  if (renderer?.domElement.parentElement) renderer.domElement.parentElement.removeChild(renderer.domElement);
  renderer?.dispose();
});
</script>

<template>
  <div ref="host" class="puppet-stage" />
</template>

<style scoped>
.puppet-stage { position: absolute; inset: 0; }
.puppet-stage :deep(canvas) { display: block; width: 100%; height: 100%; }
</style>
