import * as THREE from "three";

let preloaded = false;

export async function preloadThree(): Promise<void> {
  if (preloaded) return;
  preloaded = true;
  await Promise.resolve();
}

export function disposeScene(scene: THREE.Scene) {
  scene.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (mesh.geometry) mesh.geometry.dispose();
    if (mesh.material) {
      if (Array.isArray(mesh.material)) {
        mesh.material.forEach((m) => m.dispose());
      } else {
        mesh.material.dispose();
      }
    }
  });
}

export const FOG_DENSITY = 0.018;
export const BIRD_COUNT = 40;