import { useEffect, useRef } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import TopNavPill from './TopNavPill';
import GhostFibers from './GhostFibers';

const SHORTCUT_MAP = { d: '/', n: '/notes', t: '/tasks', c: '/calendar', a: '/analytics', s: '/settings' };

export default function AppLayout() {
  const navigate = useNavigate();
  const pendingG = useRef(false);

  useEffect(() => {
    function onKeyDown(e) {
      const tag = document.activeElement?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.isContentEditable) return;

      if (e.key === 'g') {
        pendingG.current = true;
        setTimeout(() => { pendingG.current = false; }, 800);
        return;
      }
      if (pendingG.current && SHORTCUT_MAP[e.key]) {
        navigate(SHORTCUT_MAP[e.key]);
        pendingG.current = false;
      }
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [navigate]);

  return (
    <div className="relative min-h-screen bg-[#090715] text-[#f5f3ff] overflow-x-hidden selection:bg-indigo-500/30 selection:text-white">
      {/* Background GhostFibers */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" style={{ width: '100vw', height: '100vh' }}>
        <div style={{ width: '100%', height: '100%', position: 'relative' }}>
          <GhostFibers
            lineColor="#140E35"
            glowColor="#3437A0"
            speed={0.2}
            scale={2}
            rotation={0}
            rotationSpeed={0.25}
            layers={4}
            waveAmplitude={0.015}
            waveFrequency={3}
            waveSpeed={0.15}
            layerSpeed={0.08}
            twist={0.1}
            twistFrequency={5}
            twistSpeed={1.2}
            lineFrequency={5}
            lineSpacing={2}
            lineSharpness={16}
            glowFalloff={10}
            glowIntensity={1.6}
            brightness={2}
            blueBoost={1.25}
            vignette={0.8}
            grain={0.05}
            dpr={1}
            lightMode={false}
            fps={60}
            paused={false}
          />
        </div>
        {/* Subtle dark backdrop filter to ensure all cards & typography remain clear */}
        <div className="absolute inset-0 bg-[#090715]/55 backdrop-blur-[0.5px]" />
      </div>

      {/* Floating Top Navigation Bar Pill */}
      <TopNavPill />

      {/* Main Content Workspace */}
      <main className="relative z-10 pt-20 sm:pt-24 pb-16 px-4 sm:px-6 md:px-8 max-w-7xl mx-auto">
        <Outlet />
      </main>
    </div>
  );
}
