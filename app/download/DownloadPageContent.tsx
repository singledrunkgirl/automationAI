"use client";

import { Authenticated, Unauthenticated } from "convex/react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Header from "@/app/components/Header";
import { HackWithAISVG } from "@/components/icons/hwai-svg";
import { DownloadSection, useDetectedPlatform } from "./DownloadSection";
import { downloadLinks } from "./constants";
import { WindowsIcon, LinuxIcon, AndroidIcon } from "./icons";

function AuthenticatedHeader() {
  return (
    <header className="w-full px-6 max-sm:px-4 flex-shrink-0">
      <div className="py-[10px] flex gap-10 items-center justify-between">
        <div className="flex items-center gap-2">
          <HackWithAISVG theme="dark" scale={0.15} />
          <span className="text-foreground text-xl font-semibold max-sm:text-lg">
            HackWithAI v2
          </span>
        </div>
        <Button
          asChild
          variant="ghost"
          size="default"
          className="rounded-[10px]"
        >
          <Link href="/">
            <ArrowLeft className="h-4 w-4 mr-1.5" />
            Back to Chat
          </Link>
        </Button>
      </div>
    </header>
  );
}

function DownloadContent() {
  const detected = useDetectedPlatform();
  const isMobile =
    detected?.platform === "ios" || detected?.platform === "android";

  return (
    <div className="px-4 py-8 pb-16 md:px-0">
      <div className="container mx-auto max-w-3xl space-y-8">
        <div className="text-center">
          <h1 className="mb-4 text-4xl font-bold text-card-foreground">
            {isMobile
              ? "Install HackWithAI v2"
              : "Download HackWithAI v2"}
          </h1>
          <p className="text-lg text-muted-foreground">
            {isMobile
              ? "Add the app to your home screen"
              : "Get the desktop app for the best experience"}
          </p>
        </div>

        <DownloadSection />

        {!isMobile && (
          <div className="rounded-md border bg-card p-6 shadow-lg">
            <h2 className="mb-4 text-xl font-semibold text-card-foreground">
              Desktop Downloads
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <DownloadCard
                title="Windows"
                subtitle="Agent app (.exe)"
                href={downloadLinks.windows}
                icon={<WindowsIcon />}
              />
              <DownloadCard
                title="Kali Linux"
                subtitle="Agent package (.deb)"
                href={downloadLinks.linuxDeb}
                icon={<LinuxIcon />}
              />
              <DownloadCard
                title="Linux"
                subtitle="Portable agent (.AppImage)"
                href={downloadLinks.linuxAppImage}
                icon={<LinuxIcon />}
              />
              <DownloadCard
                title="Android"
                subtitle="Agent app (.apk)"
                href={downloadLinks.androidApk}
                icon={<AndroidIcon />}
              />
            </div>
            <p className="mt-4 text-sm text-muted-foreground">
              Install the downloaded app to connect a local machine for Agent
              mode.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export function DownloadPageContent() {
  return (
    <div className="min-h-screen bg-background">
      <Authenticated>
        <AuthenticatedHeader />
        <DownloadContent />
      </Authenticated>
      <Unauthenticated>
        <Header hideDownload />
        <DownloadContent />
      </Unauthenticated>
    </div>
  );
}

function DownloadCard({
  title,
  subtitle,
  href,
  icon,
}: {
  title: string;
  subtitle: string;
  href: string;
  icon: React.ReactNode;
}) {
  return (
    <a
      href={href}
      download
      className="flex items-center gap-3 rounded-md border bg-background p-4 transition-colors hover:bg-accent"
    >
      <div className="text-muted-foreground">{icon}</div>
      <div>
        <div className="font-medium text-card-foreground">{title}</div>
        <div className="text-sm text-muted-foreground">{subtitle}</div>
      </div>
    </a>
  );
}
