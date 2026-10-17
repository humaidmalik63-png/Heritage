import React, { useRef, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Stars, Float, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';

// Animated architectural arch form
const ArchForm: React.FC<{ position: [number, number, number]; scale: number; opacity: number }> = ({ position, scale, opacity }) => {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.05;
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.03) * 0.05;
    }
  });

  return (
    <Float speed={0.8} rotationIntensity={0.2} floatIntensity={0.3}>
      <mesh ref={meshRef} position={position} scale={scale}>
        <torusGeometry args={[1, 0.02, 16, 80, Math.PI]} />
        <meshStandardMaterial
          color="#c9a84c"
          transparent
          opacity={opacity}
          emissive="#8a6f3c"
          emissiveIntensity={0.3}
        />
      </mesh>
    </Float>
  );
};

// Floating dome silhouette
const DomeSilhouette: React.FC = () => {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.03;
      groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.4) * 0.08;
    }
  });

  return (
    <group ref={groupRef} position={[2.5, 0, -2]}>
      {/* Dome */}
      <mesh position={[0, 0.6, 0]}>
        <sphereGeometry args={[0.8, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <MeshDistortMaterial
          color="#1c1916"
          wireframe
          distort={0.1}
          speed={0.5}
          transparent
          opacity={0.5}
        />
      </mesh>
      {/* Base */}
      <mesh position={[0, 0, 0]}>
        <cylinderGeometry args={[0.9, 1.1, 0.3, 32]} />
        <meshStandardMaterial color="#1c1916" transparent opacity={0.6} />
      </mesh>
      {/* Minaret left */}
      <mesh position={[-1.4, 0.6, 0]}>
        <cylinderGeometry args={[0.07, 0.1, 1.8, 8]} />
        <meshStandardMaterial color="#1c1916" transparent opacity={0.5} />
      </mesh>
      {/* Minaret right */}
      <mesh position={[1.4, 0.6, 0]}>
        <cylinderGeometry args={[0.07, 0.1, 1.8, 8]} />
        <meshStandardMaterial color="#1c1916" transparent opacity={0.5} />
      </mesh>
      {/* Gold trim ring */}
      <mesh position={[0, 0.62, 0]}>
        <torusGeometry args={[0.82, 0.015, 8, 64]} />
        <meshStandardMaterial color="#c9a84c" emissive="#c9a84c" emissiveIntensity={0.4} />
      </mesh>
    </group>
  );
};

// Atmospheric particles
const AtmosphericParticles: React.FC = () => {
  const count = 60;
  const positions = React.useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3 + 0] = (Math.random() - 0.5) * 12;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 6;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 8;
    }
    return arr;
  }, []);

  const pointsRef = useRef<THREE.Points>(null);

  useFrame((state) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y = state.clock.elapsedTime * 0.01;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color="#c9a84c" size={0.03} transparent opacity={0.4} sizeAttenuation />
    </points>
  );
};

export const HeroCanvas: React.FC = () => {
  return (
    <div className="hero-canvas">
      <Canvas
        camera={{ position: [0, 0, 6], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          {/* Ambient illumination */}
          <ambientLight intensity={0.3} />
          <pointLight position={[4, 3, 2]} intensity={0.8} color="#c9a84c" />
          <pointLight position={[-4, -2, -1]} intensity={0.4} color="#8a6f3c" />
          <directionalLight position={[0, 5, 3]} intensity={0.4} color="#f2ede4" />

          {/* Stars background */}
          <Stars radius={80} depth={50} count={800} factor={2} saturation={0} fade speed={0.3} />

          {/* Atmospheric golden particles */}
          <AtmosphericParticles />

          {/* Dome silhouette */}
          <DomeSilhouette />

          {/* Decorative arches */}
          <ArchForm position={[-3, 0.5, -1]} scale={1.8} opacity={0.15} />
          <ArchForm position={[1, -0.8, -2]} scale={1.2} opacity={0.1} />
          <ArchForm position={[-1.5, -1.5, -3]} scale={2.5} opacity={0.07} />

          {/* Ground plane for atmosphere */}
          <mesh position={[0, -2, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[20, 20]} />
            <meshStandardMaterial
              color="#0d0c0a"
              transparent
              opacity={0.8}
              roughness={1}
            />
          </mesh>
        </Suspense>
      </Canvas>
    </div>
  );
};
