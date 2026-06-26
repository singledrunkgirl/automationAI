import type { FC } from "react";
import Image from "next/image";

interface HackWithAISVGProps {
  theme: "dark" | "light";
  scale?: number;
}

export const HackWithAISVG: FC<HackWithAISVGProps> = ({
  scale = 1,
}) => {
  const width = Math.round(189 * scale);
  const height = Math.round(194 * scale);

  return (
    <Image
      src="/logo-mark.png"
      alt="HackWithAI logo"
      width={width}
      height={height}
      className="object-contain"
      priority
    />
  );
};
