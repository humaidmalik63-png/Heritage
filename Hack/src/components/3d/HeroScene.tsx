import { Canvas } from "@react-three/fiber";
import { OrbitControls, Environment, useGLTF, useAnimations } from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { useReducedMotion } from "@lib/motion";

function Monument() {
  const group = useRef<THREE.Group>(null);
  const reduced = useReducedMotion();

  // Procedural monument built from primitives — no external asset dependency.
  const geometry = useMemo(() => new THREE.BoxGeometry(1, 1, 1), []);

  useEffect(() => {
    if (!group.current || reduced) return;
    const rot = group.current.rotation;
    let frame = 0;
    const tick = () => {
      frame += 0.004;
      rot.y = Math.sin(frame) * 0.15;
      rot.x = Math.cos(frame * 0.6) * 0.05;
      requestAnimationFrame(tick);
    };
    const id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, [reduced]);

  return (
    <group ref={group} position={[0, 0, 0]}>
      <mesh geometry={geometry} position={[0, 1.4, 0]}>
        <meshStandardMaterial color="#D4B483" metalness={0.4} roughness={0.55} />
      </mesh>
      <mesh geometry={geometry} position={[0, 0.7, 0]} scale={[1.4, 1.4, 1.4]}>
        <meshStandardMaterial color="#1A1D27" metalness={0.3} roughness={0.7} />
      </mesh>
      <mesh geometry={geometry} position={[0, 0, 0]} scale={[1.8, 1.8, 1.8]}>
        <meshStandardMaterial color="#11131A" metalness={0.2} roughness={0.85} />
      </mesh>
    </group>
  );
}

export default function HeroScene() {
  const reduced = useReducedMotion();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setReady(true), 300);
    return () => clearTimeout(t);
  }, []);

  if (reduced) {
    return (
      <div className="absolute inset-0 bg-gradient-to-b from-heritage-deep to-heritage-surface">
        <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_50%_40%,rgba(212,180,131,0.18),transparent_60%)]" />
      </div>
    );
  }

  return (
    <Suspense
      fallback={
        <div className="absolute inset-0 bg-gradient-to-b from-heritage-deep to-heritage-surface">
          <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_50%_40%,rgba(212,180,131,0.18),transparent_60%)]" />
        </div>
      }
    >
      <Canvas
        camera={{ position: [0, 2.5, 6], fov: 45 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <fog attach="fog" args={["#05070C", 8, 28]} />
        <ambientLight intensity={0.5} />
        <directionalLight position={[4, 6, 4]} intensity={1.2} color="#E8D1CB" />
        <directionalLight position={[-4, 3, -4]} intensity={0.4} color="#C4C7CE" />

        {ready && <Monument />}

        <Environment preset="city" />

        <OrbitControls
          enableZoom={false}
          enablePan={false}
          minPolarAngle={Math.PI / 2.5}
          maxPolarAngle={Math.PI / 1.9}
          autoRotate
          autoRotateSpeed={0.6}
        />
      </Canvas>
    </Suspense>
  );
}