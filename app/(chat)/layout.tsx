"use client";

import { ChatLayout } from "@/app/components/ChatLayout";

export default function ChatRouteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="h-dvh min-h-0 flex flex-col bg-background overflow-hidden">
      <ChatLayout>{children}</ChatLayout>
    </div>
  );
}
