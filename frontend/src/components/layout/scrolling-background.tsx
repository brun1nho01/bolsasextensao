import { motion, useScroll, useTransform, useSpring } from "framer-motion";
import { useRef } from "react";

import fotouenf2 from "@/assets/fotouenf2.jpg";
import fotouenf4 from "@/assets/fotouenf4.jpg";
import fotouenf1 from "@/assets/fotouenf1.jpg";
import fotouenf3 from "@/assets/fotouenf3.jpeg";

const images = [fotouenf1, fotouenf2, fotouenf3, fotouenf4];

// Define os pontos de início e fim da visibilidade de cada imagem (0.0 = topo, 1.0 = final)
const imageRanges: [number, number][] = [
  [0.0, 0.25], // Imagem 1: Visível nos primeiros 25% da rolagem
  [0.25, 0.55], // Imagem 2: Visível dos 25% aos 60% (duração maior)
  [0.55, 0.8], // Imagem 3: Agora começa a transição a partir de 60%
  [0.8, 1.0], // Imagem 4: Visível nos últimos 20%
];

interface ScrollingBackgroundProps {
  children: React.ReactNode;
}

const ImageLayer = ({
  src,
  progress,
  range,
}: {
  src: string;
  progress: any;
  range: [number, number];
}) => {
  const opacity = useTransform(
    progress,
    [range[0] - 0.15, range[0], range[1], range[1] + 0.15],
    [0, 1, 1, 0]
  );

  return (
    <motion.div className="absolute inset-0 h-full w-full" style={{ opacity }}>
      <img src={src} alt="Background" className="h-full w-full object-cover" />
      <div className="absolute inset-0 bg-black/60" />
    </motion.div>
  );
};

export function ScrollingBackgroundProvider({
  children,
}: ScrollingBackgroundProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: scrollRef,
    offset: ["start start", "end end"],
  });

  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 40,
    damping: 50,
    restDelta: 0.001,
  });

  return (
    <div ref={scrollRef} className="relative">
      <div className="sticky top-0 h-screen w-full">
        {images.map((src, index) => {
          const range = imageRanges[index];
          return (
            <ImageLayer
              key={src}
              src={src}
              progress={smoothProgress}
              range={range}
            />
          );
        })}
      </div>
      <div className="relative z-10 -mt-[100vh]">{children}</div>
    </div>
  );
}
